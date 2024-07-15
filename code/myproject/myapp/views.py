from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import openai
from PIL import Image
from io import BytesIO
import base64
from .models import APICall  # Adjust this import statement
from .serializers import APICallSerializer  # Ensure serializers are correctly imported



# Set up your OpenAI API key
openai.api_key = "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"

def process_response(response_text):
    response_lines = response_text.split('\n')
    code_lines = []
    explanation_lines = []
    is_code = False

    for line in response_lines:
        if "```" in line:
            is_code = not is_code
            continue
        if is_code:
            code_lines.append(line)
        else:
            explanation_lines.append(line)

    code = "\n".join(code_lines).strip()
    explanation = "\n".join(explanation_lines).strip()

    result = {}
    if code:
        result["code"] = code
    if explanation:
        result["explanation"] = explanation

    return result

@api_view(['POST'])
def prompt_to_code(request):
    data = request.data
    prompt = data.get('prompt')
    lang = data.get('lang')
    ip_address = request.META.get('REMOTE_ADDR')

    if not prompt:
        return Response({"Message": "Prompt is mandatory", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

    combined_prompt = (f"Please respond to the following query. If it's a coding question, provide the source code in {lang}. "
                       f"If it needs an explanation, provide a detailed explanation. If both are required, provide both:\n\n{prompt}\n\n"
                       f"Language: {lang}" if lang else f"Please respond to the following query. If it's a coding question, provide the source code. "
                                                        f"If it needs an explanation, provide a detailed explanation. If both are required, provide both:\n\n{prompt}")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert software engineer."},
            {"role": "user", "content": combined_prompt}
        ],
        temperature=0.5,
        max_tokens=1500,
    )

    response_text = response.choices[0].message['content'].strip()
    result = process_response(response_text)

    api_call = APICall.objects.create(
        prompt=prompt,
        lang=lang,
        ip_address=ip_address,
        response_data=result
    )
    serializer = APICallSerializer(api_call)

    return Response({"Data": result, "Message": "Success", "Status": 1}, status=status.HTTP_200_OK)



import openai
import base64
from io import BytesIO
from PIL import Image
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import time

# Function to process the response
def process_response(response_text):
    response_lines = response_text.split('\n')
    code_lines = []
    explanation_lines = []
    is_code = False

    for line in response_lines:
        if "```" in line:
            is_code = not is_code
            continue
        if is_code:
            code_lines.append(line)
        else:
            explanation_lines.append(line)

    code = "\n".join(code_lines).strip()
    explanation = "\n".join(explanation_lines).strip()

    result = {}
    if code:
        result["code"] = code
    if explanation:
        result["explanation"] = explanation

    return result

# Function to resize and compress the image
def resize_and_compress_image(image_data, max_size=(300, 300), quality=20):
    image = Image.open(BytesIO(image_data))
    image.thumbnail(max_size, Image.ANTIALIAS)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()

@api_view(['POST'])
def design_to_code(request):
    prompt = request.data.get('prompt')
    image = request.FILES.get('image')
    ip_address = request.data.get('ip_address')
    lang = request.data.get('lang', '')

    if not prompt or not image or not ip_address:
        return Response({"Message": "Prompt, image, and IP address are mandatory", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Resize and compress the image before encoding
        image_data = resize_and_compress_image(image.read())
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Truncate the prompt if it's too long
        max_prompt_length = 1000  # Adjust this length as needed
        if len(prompt) > max_prompt_length:
            prompt = prompt[:max_prompt_length] + '...'

        # Construct the user message including the base64 image
        user_message = {
            "type": "text",
            "text": prompt
        }
        image_message = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        }

        # Constructing the payload for OpenAI API
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "user", "content": [user_message, image_message]}
            ],
            "max_tokens": 1500,
            "temperature": 0.5
        }

        # Include lang parameter if provided
        if lang:
            payload["messages"][0]["content"].append({"type": "text", "text": f"Language: {lang}"})

        # Set timeout and retry logic
        timeout = 60  # seconds
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                response = openai.ChatCompletion.create(**payload, timeout=timeout)
                response_text = response['choices'][0]['message']['content'].strip()
                result = process_response(response_text)
                return Response({"Data": result, "IP_Address": ip_address, "Message": "Success", "Status": 1}, status=status.HTTP_200_OK)
            except openai.error.Timeout:
                retries += 1
                if retries >= max_retries:
                    return Response({"Message": "Request timed out after multiple attempts. Please try again later.", "Status": 0}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                time.sleep(2 ** retries)  # Exponential backoff
            except Exception as e:
                return Response({"Message": f"Error: {str(e)}", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Message": "Unknown error occurred. Please try again later.", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"Message": f"Image processing failed: {e}", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)


################################################
import openai
import base64
from io import BytesIO
from PIL import Image
import pytesseract
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import time


# Ensure pytesseract can find the tesseract executable
pytesseract.pytesseract.tesseract_cmd = '../../tesseract/tesseract.exe'

# Function to process the response from OpenAI
def process_response(response_text):
    response_lines = response_text.split('\n')
    code_lines = []
    explanation_lines = []
    is_code = False

    for line in response_lines:
        if "```" in line:
            is_code = not is_code
            continue
        if is_code:
            code_lines.append(line)
        else:
            explanation_lines.append(line)

    code = "\n".join(code_lines).strip()
    explanation = "\n".join(explanation_lines).strip()

    result = {}
    if code:
        result["code"] = code
    if explanation:
        result["explanation"] = explanation

    return result

# Function to resize and compress the image
def resize_and_compress_image(image_data, max_size=(300, 300), quality=20):
    image = Image.open(BytesIO(image_data))
    image.thumbnail(max_size, Image.ANTIALIAS)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()

# Function to extract text from image using Tesseract OCR
def extract_text_from_image(image_data):
    image = Image.open(BytesIO(image_data))
    text = pytesseract.image_to_string(image)
    return text.strip()

@api_view(['POST'])
def image_to_solve(request):
    prompt = request.data.get('prompt')
    image = request.FILES.get('image')
    ip_address = request.data.get('ip_address')
    lang = request.data.get('lang', '')

    if not prompt or not image or not ip_address:
        return Response({"Message": "Prompt, image, and IP address are mandatory", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Resize and compress the image before encoding
        image_data = resize_and_compress_image(image.read())

        # Extract text from the image using Tesseract OCR
        extracted_text = extract_text_from_image(image_data)

        # Combine prompt and extracted text
        combined_text = f"{prompt}\n\n{extracted_text}".strip()

        # Constructing the payload for OpenAI API
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "user", "content": combined_text}
            ],
            "max_tokens": 1500,
            "temperature": 0.5
        }

        # Include language information if provided
        if lang:
            payload["messages"].append({"role": "user", "content": f"Language: {lang}"})

        # Set timeout and retry logic
        timeout = 60  # seconds
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                response = openai.ChatCompletion.create(**payload, timeout=timeout)
                response_text = response['choices'][0]['message']['content'].strip()
                result = process_response(response_text)

                return Response({"Data": result, "IP_Address": ip_address, "Message": "Success", "Status": 1}, status=status.HTTP_200_OK)
            
            except openai.error.Timeout:
                retries += 1
                if retries >= max_retries:
                    return Response({"Message": "Request timed out after multiple attempts. Please try again later.", "Status": 0}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                time.sleep(2 ** retries)  # Exponential backoff
            
            except Exception as e:
                return Response({"Message": f"Error: {str(e)}", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Message": "Unknown error occurred. Please try again later.", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"Message": f"Image processing failed: {e}", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)



################################################
import openai
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import APICall
from .serializers import APICallSerializer

@api_view(['POST'])
def convert_code(request):
    try:
        prompt = request.data.get('prompt')
        lang = request.data.get('lang')
        ip_address = request.data.get('ip_address', request.META.get('REMOTE_ADDR'))

        if not prompt or not lang:
            return Response({"Message": "Prompt and language are mandatory", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

        # Construct the payload for OpenAI API
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "user", "content": f"Convert the following code to {lang}:\n\n{prompt}"}
            ],
            "max_tokens": 1500,
            "temperature": 0.5
        }

        # Set timeout and retry logic
        timeout = 60  # seconds
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                response = openai.ChatCompletion.create(**payload, timeout=timeout)
                response_text = response['choices'][0]['message']['content'].strip()
                
                # Save API call to the database
                api_call = APICall.objects.create(
                    prompt=prompt,
                    lang=lang,
                    ip_address=ip_address,
                    response_data={"response": response_text}
                )
                serializer = APICallSerializer(api_call)
                return Response({"Data": serializer.data, "Message": "Success", "Status": 1}, status=status.HTTP_200_OK)
            except openai.error.Timeout:
                retries += 1
                if retries >= max_retries:
                    return Response({"Message": "Request timed out after multiple attempts. Please try again later.", "Status": 0}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                time.sleep(2 ** retries)  # Exponential backoff
            except Exception as e:
                return Response({"Message": f"Error: {str(e)}", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Message": "Unknown error occurred. Please try again later.", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"Message": f"Server error: {e}", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
################################################
import base64
import time
from io import BytesIO
import fitz  # PyMuPDF for PDF handling
from docx import Document  # Correct import for python-docx's Document class
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import APICall
from .serializers import APICallSerializer

@api_view(['POST'])
def solve_with_doc(request):
    document = request.FILES.get('document')
    prompt = request.data.get('prompt', '')
    lang = request.data.get('lang', '')
    ip_address = request.META.get('REMOTE_ADDR')

    if not document:
        return Response({"Message": "Document file is required", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Read the document content
        document_data = document.read()

        # Determine the document type (PDF or DOCX)
        if document.name.endswith('.pdf'):
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(document_data)
        elif document.name.endswith('.doc') or document.name.endswith('.docx'):
            # Extract text from DOCX
            extracted_text = extract_text_from_docx(document_data)
        else:
            return Response({"Message": "Unsupported file format. Only .doc, .docx, or .pdf files are supported", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

        # Combine prompt and extracted text
        combined_text = f"{prompt}\n\n{extracted_text}".strip()

        # Constructing the payload for OpenAI API
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "user", "content": combined_text}
            ],
            "max_tokens": 1500,
            "temperature": 0.5
        }

        # Include language information if provided
        if lang:
            payload["messages"].append({"role": "user", "content": f"Language: {lang}"})

        # Set timeout and retry logic
        timeout = 60  # seconds
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                response = openai.ChatCompletion.create(**payload, timeout=timeout)
                response_text = response['choices'][0]['message']['content'].strip()
                result = {"response": response_text}

                # Save API call to the database
                with transaction.atomic():
                    api_call = APICall.objects.create(
                        prompt=prompt,
                        lang=lang,
                        document=document,
                        ip_address=ip_address,
                        response_data=result
                    )
                    serializer = APICallSerializer(api_call)

                return Response({"Data": serializer.data, "Message": "Success", "Status": 1}, status=status.HTTP_200_OK)
            except openai.error.Timeout:
                retries += 1
                if retries >= max_retries:
                    return Response({"Message": "Request timed out after multiple attempts. Please try again later.", "Status": 0}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                time.sleep(2 ** retries)  # Exponential backoff
            except Exception as e:
                return Response({"Message": f"Error: {str(e)}", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Message": "Unknown error occurred. Please try again later.", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"Message": f"Document processing failed: {e}", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)


def extract_text_from_pdf(pdf_data):
    try:
        # Open PDF file from memory
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
        
        # Initialize an empty string to store extracted text
        text = ""
        
        # Iterate through each page and extract text
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        
        # Close the PDF document
        pdf_document.close()
        
        return text.strip()
    
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    
def extract_text_from_docx(docx_data):
    try:
        # Load the DOCX file from memory
        doc = Document(BytesIO(docx_data))
        
        # Initialize an empty string to store extracted text
        text = ""
        
        # Iterate through each paragraph and extract text
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        return text.strip()
    
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

#################################################
@api_view(['POST'])
def code_explainer(request):
    code = request.data.get('code', '')
    ip_address = request.META.get('REMOTE_ADDR')

    if not code:
        return Response({"Message": "Code input is required", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

    # Define a clear prompt indicating the API's goal
    prompt = "Code Explanation:\n\n"
    prompt += f"Input Code:\n{code}\n\n"

    try:
        # Constructing the payload for OpenAI API
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.5
        }

        # Set timeout and retry logic
        timeout = 60  # seconds
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                response = openai.ChatCompletion.create(**payload, timeout=timeout)
                response_text = response['choices'][0]['message']['content'].strip()
                result = {"explanation": response_text}

                # Save API call to the database
                with transaction.atomic():
                    api_call = APICall.objects.create(
                        prompt=prompt,
                        ip_address=ip_address,
                        response_data=result
                    )
                    serializer = APICallSerializer(api_call)

                return Response({"Data": serializer.data, "Message": "Success", "Status": 1}, status=status.HTTP_200_OK)
            except openai.error.Timeout:
                retries += 1
                if retries >= max_retries:
                    return Response({"Message": "Request timed out after multiple attempts. Please try again later.", "Status": 0}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                time.sleep(2 ** retries)  # Exponential backoff
            except Exception as e:
                return Response({"Message": f"Error: {str(e)}", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Message": "Unknown error occurred. Please try again later.", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"Message": f"Code explanation failed: {e}", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

##################################################
import base64
import time
import json
from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import APICall
from .serializers import APICallSerializer

@api_view(['POST'])
def detect_bugs(request):
    code = request.data.get('code', '')
    ip_address = request.META.get('REMOTE_ADDR')

    if not code:
        return Response({"Message": "Code snippet is required", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Constructing the payload for OpenAI API
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "user", "content": code}
            ],
            "max_tokens": 1500,
            "temperature": 0.5
        }

        # Set timeout and retry logic
        timeout = 60  # seconds
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                response = openai.ChatCompletion.create(**payload, timeout=timeout)
                response_text = response['choices'][0]['message']['content'].strip()
                result = {"bugs_found": response_text}

                # Save API call to the database
                with transaction.atomic():
                    api_call = APICall.objects.create(
                        prompt="Bug Detector",
                        code=code,
                        ip_address=ip_address,
                        response_data=result
                    )
                    serializer = APICallSerializer(api_call)

                return Response({
                    "Data": serializer.data,
                    "Message": "Success",
                    "Status": 1,
                    "Prompt": "This API is a bug detector. It identifies bugs in provided code snippets."
                }, status=status.HTTP_200_OK)
            except openai.error.Timeout:
                retries += 1
                if retries >= max_retries:
                    return Response({"Message": "Request timed out after multiple attempts. Please try again later.", "Status": 0}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                time.sleep(2 ** retries)  # Exponential backoff
            except Exception as e:
                return Response({"Message": f"Error: {str(e)}", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Message": "Unknown error occurred. Please try again later.", "Status": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"Message": f"Bug detection failed: {e}", "Status": 0}, status=status.HTTP_400_BAD_REQUEST)
