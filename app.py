from chalice import Chalice, Response
import requests
import json
import curlify
import io
import cgi
from io import BytesIO
import boto3
import time
import os
from dotenv import load_dotenv

app = Chalice(app_name='chalice-api-sample')
logs_client = boto3.client('logs')

load_dotenv()


WEB_LOG_GROUP = "web-logs"
MOBILE_LOG_GROUP = "mobile-logs"

authToken = os.getenv('AUTH_TOKEN')
accessToken = os.getenv('ACCESS_TOKEN')



@app.route('/api_test', methods=['POST'], cors=True)
def api_test():
    request = app.current_request
    body = request.json_body
    print("Request body:", body)

    url = body.get('url')
    method = body.get('method', 'POST').upper()
    params = body.get('params', {})
    extra_data = body.get('extra_data', {})
    data = body.get('data')
    
    
    print('Daata',data)
    
    if not url:
        return {'error': 'No URL provided'}
    
    parameters = extra_data.get('parameters')

    if parameters:
        params[parameters] = accessToken

    headers = {
        'Authorization': f"OAuth {accessToken}" if extra_data.get('useAccessToken') else f"Bearer {authToken}",
        'file_offset': '0',
        
    }
    
    if extra_data.get('isContent'):
        headers['Content-Type'] = "text/plain"   
        
    try:
        if data:
            response = requests.request(method=method, url=url, params=params, headers=headers, data=json.dumps(data).encode('utf-8'))
        else:
            response = requests.request(method=method, url=url, params=params, headers=headers)

        return {
            'status_code': response.status_code,
            'response': response.json(),
        }

    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

    except ValueError:
        return {'error': 'Failed to parse response JSON'}
    
    
    
@app.route('/upload_media', methods=['POST'],content_types=['multipart/form-data'], cors=True)
def upload_media():
    request = app.current_request
    print(request.raw_body)
    rfile = BytesIO(request.raw_body)
    content_type = request.headers['Content-Type']
    _, parameters = cgi.parse_header(content_type)
    parameters['boundary'] = parameters['boundary'].encode('utf-8')
    parsed = cgi.parse_multipart(rfile, parameters)
    
    file_content = parsed.get('file')[0]
    url = parsed.get('url')[0]
    headers = {
        'Authorization': f"OAuth {accessToken}",
        'file_offset': '0',
        'Content-Type': 'text/plain'
    }    

    
    
    try:
        response = requests.post(
            url=url,
            headers=headers,
            data=file_content
        )
    
        
        return Response(
            status_code=response.status_code,
            body={
                'message': 'File uploaded successfully.',
                'response_data': response.json()
            }
        )
    except requests.RequestException as e:
        return Response(
            status_code=500,
            body={'error': f'Error uploading file to {url}', 'details': str(e)},
        )    


@app.route('/message_templates', methods=['POST'], cors=True)
def message_templates():
    request = app.current_request
    body = request.json_body
    
    formattedBody = body.get('formattedBody')
    
    print('Formatted Body', formattedBody)
    
    headers = {
        'Authorization': f"Bearer {accessToken}",
        'Content-Type': 'application/json'
    }
       
    url = 'https://graph.facebook.com/v21.0/397892343406101/message_templates'
    
    try:
        response = requests.post(
            url=url,
            headers=headers,
            data=formattedBody
        )
    
        
        return Response(
            status_code=response.status_code,
            body={
                'message': 'Mesaage Template uploaded successfully.',
                'response_data': response.json()
            }
        )
    except requests.RequestException as e:
        return Response(
            status_code=500,
            body={ 'details': str(e)},
        )    


@app.route('/get_message_templates', methods=['POST'], cors=True)
def get_message_templates():
    request = app.current_request
    body = request.json_body
    params = body.get('params', {})
    

    try:
        
        
        api_url = 'https://graph.facebook.com/v21.0/397892343406101/message_templates'

        
        headers = {
            'Authorization':f"Bearer {accessToken}"
        }

        
        response = requests.get(api_url, params=params, headers=headers)

        if response.status_code == 200:
            
            return {
                "status": "success",
                "data": response.json()
            }
        else:
           
            return {
                "status": "error",
                "message": f"Failed to fetch message templates. Error: {response.text}"
            }

    except Exception as e:
       
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }

 
@app.route('/delete_message_templates', methods=['POST'], cors=True)
def delete_template():
    request = app.current_request
    body = request.json_body
    params = body.get('params', {})
    
    try:
        
        
        api_url = 'https://graph.facebook.com/v21.0/397892343406101/message_templates'

        
        headers = {
            'Authorization':f"Bearer {accessToken}"
        }

        
        response = requests.delete(api_url, params=params, headers=headers)

        if response.status_code == 200:
            
            return {
                "status": "success",
                "data": response.json()
            }
        else:
           
            return {
                "status": "error",
                "message": f"Failed to fetch message templates. Error: {response.text}"
            }

    except Exception as e:
       
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }


@app.route('/logsInfo', methods=['POST'], cors=True)
def logsInfo():
    request = app.current_request
    body = request.json_body  
    source = body.get('source')
    device_info = body.get('device_info')
    log_type = body.get('log_type')
    log_message = body.get('log_message')
    env_type = body.get('env_type') 
    
    if source == 'desktop' or source == 'mobile':
        log_group = WEB_LOG_GROUP
    elif source == 'android' or source == 'ios':
        log_group = MOBILE_LOG_GROUP
    else:
        return {"status": "error", "message": "Invalid source"}
    

    log_stream_name = f"{source}-logs"

    log_event = {
        "timestamp": int(round(time.time() * 1000)),
        "message": json.dumps({
            "source": source,
            "device_info": device_info,
            "log_type": log_type,
            "log_message": log_message,
            "env_type": env_type
        })
    }

    try:
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            logStreamNamePrefix=log_stream_name
        )
        print('response is', response)
        log_streams = response.get('logStreams', [])
        sequence_token = None
        
        if log_streams:
            sequence_token = log_streams[0].get('uploadSequenceToken')
        else:
            logs_client.create_log_stream(logGroupName=log_group, logStreamName=log_stream_name)                     
        if sequence_token:
            response = logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream_name,
                logEvents=[log_event],
                sequenceToken=sequence_token
            )
        else:
            response = logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream_name,
                logEvents=[log_event]
            )
        
        return {"status": "success", "log_group": log_group, "log_stream": log_stream_name}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    

def replaceplaceholders(text, data):
    for key, value in data.items():
        placeholder = f"{{{key}}}"
        text = text.replace(placeholder, value)
    return text    
    
@app.route('/testTemplate', methods=['POST'], cors=True)
def testTemplate():
    request = app.current_request
    body = request.json_body  
    config_data = body.get('config_data')
    to = body.get('to')
    template_id = body.get('template_id')
    data = body.get('data')
    
    headers = {
        'Authorization': f"Bearer {accessToken}", 
        'Content-Type': 'application/json'  
    }
    
    # WhatsApp body
    whatsappBody = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
       "type": "template",
        "template": {
            "name": template_id,
            "language": {
                "code": "en_US"
            },
            "components": []
        }
    }
    
       
    if 'header_config' in config_data:
        header_component = {
            "type": "header",
            "parameters": []
        }
        for header in config_data['header_config']:
            if header['type'] == 'text':
                header_component['parameters'].append({
                    "type": "text",
                    "text": replaceplaceholders(header['text'], data),
                    "parameter_name": replaceplaceholders(header['text'], data)
                })
            elif header['type'] == 'image':
                header_component['parameters'].append({
                    "type": "image",
                    "image": {
                        "link": header['link']
                    }
                })
        whatsappBody['template']['components'].append(header_component)
    
    
    if 'body_config' in config_data:
        body_component = {
            "type": "body",
            "parameters": []
        }
        for body in config_data['body_config']:
            if body['type'] == 'text':
                body_component['parameters'].append({
                    "type": "text",
                    "text": replaceplaceholders(body['text'], data),
                    "parameter_name": replaceplaceholders(body['text'], data),
                })
        whatsappBody['template']['components'].append(body_component)
    
    
    if 'button_config' in config_data:
        button_component = {
            "type": "button",
            "parameters": []
        }
        for button in config_data['button_config']:
            if button['sub_type'] == 'url':
                button_component['parameters'].append({
                    "type": "button",
                    "sub_type": "url",
                    "index": button['index'],
                    "parameters": [{
                        "type": "text",
                        "text": replaceplaceholders(button['url'], data)
                    }]
                })
            elif  button['sub_type'] == None:
                button_component['parameters'].append({
                    "type": "button",
                    "index": button['index'],
                    "parameters": [{
                        "type": "text",
                        "text": replaceplaceholders(button['url'], data)
                    }]
                })
            else:
                 button_component['parameters'].append({
                    "type": "button",
                    "index": button['index'],
                    "parameters": [{
                        "type": "text",
                        "text": replaceplaceholders(button['url'], data)
                    }]
                })                    
        whatsappBody['template']['components'].append(button_component)
        
    print('whatsapp body is',whatsappBody)
        
    url ="https://graph.facebook.com/v21.0/427551523767916/messages"
    
    try:
        response = requests.post(url=url, headers=headers, json=whatsappBody)
        return {
            'status_code': response.status_code,
            'response': response.json(),
        }
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except ValueError:
        return {'error': 'Failed to parse response JSON'}    
    
    
@app.route('/testUtilityTemplate', methods=['POST'], cors=True)
def testTemplate():
    request = app.current_request
    body = request.json_body  
    config_data = body.get('config_data')
    to = body.get('to')
    template_id = body.get('template_id')
    data = body.get('data')
    
    headers = {
        'Authorization': f"Bearer {accessToken}", 
        'Content-Type': 'application/json'  
    }
    
    # WhatsApp body
    whatsappBody = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
       "type": "template",
        "template": {
            "name": template_id,
            "language": {
                "code": "en_US"
            },
            "components": []
        }
    }
    
       
    if 'header_config' in config_data:
        header_component = {
            "type": "header",
            "parameters": []
        }
        for header in config_data['header_config']:
            if header['type'] == 'text':
                header_component['parameters'].append({
                    "type": "text",
                    "text": replaceplaceholders(header['text'], data),
                    "parameter_name": replaceplaceholders(header['text'], data)
                })
            elif header['type'] == 'image':
                header_component['parameters'].append({
                    "type": "image",
                    "image": {
                        "link": header['link']
                    }
                })
        whatsappBody['template']['components'].append(header_component)
    
    
    if 'body_config' in config_data:
        body_component = {
            "type": "body",
            "parameters": []
        }
        for body in config_data['body_config']:
            if body['type'] == 'text':
                body_component['parameters'].append({
                    "type": "text",
                    "text": replaceplaceholders(body['text'], data),
                    "parameter_name": replaceplaceholders(body['text'], data),
                })
        whatsappBody['template']['components'].append(body_component)
    
    
    
        
    print('whatsapp body is',whatsappBody)
        
    url ="https://graph.facebook.com/v21.0/427551523767916/messages"
    
    try:
        response = requests.post(url=url, headers=headers, json=whatsappBody)
        return {
            'status_code': response.status_code,
            'response': response.json(),
        }
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except ValueError:
        return {'error': 'Failed to parse response JSON'}    
 
        

   
        
