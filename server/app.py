from flask import Flask, Response, jsonify, request
import google.generativeai as genai
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import re
import random

# Read API key from secrets
with open(r"secrets/gemini_key.txt", "r", encoding="utf-8") as file:
    key = file.read()

# Configure the Gemini model
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Setup Flask API
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

#generates a json object of questions and answers given a website, uses google genai
@app.route('/qmaker', methods=['POST'])
def qmaker():
    print('request received')
    data = request.get_json()
    if not data or 'url' not in data:
        response = jsonify({"error": "Missing 'url' field"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 400

    
    text = data['url']

    # Web scrape text from the provided URL
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(text, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)  # Extracts visible text
    else:
        return jsonify({"error": f"Unable to fetch page (Status Code: {response.status_code})"}), 400

    # Generate questions and answers using Gemini API
    prompt = (
        "Generate 1 question and its 3 multiple choice answers based on the following text, only fetch informatiom relating to the main topics of the text. Only one answer should be correct, the rest should be wrong. "
        "Only include the question and answers in the following JSON format, no filler:\n"
        "Each question and answer should only be about 10 words each"
        "{'question': '...', 'answers': [{'answer': '...', 'correct': true}, {'answer': '...', 'correct': false}, ...]}"
        "If there is an error or the content is not meaningful, respond with: {'error': 'there was an error with your request'}\n"
        f"Text:\n{text}"
    )

    
    response = model.generate_content(prompt).text
    response = "{" + re.search(r"\{(.*)\}", response).group(1) + "}"
    response = response.replace("'", '"')
    print(response)

    # Ensure the response is valid JSON
    parsed_response = json.loads(response)
    response = jsonify(parsed_response)
    response.headers.add("Access-Control-Allow-Origin", "*")  # Ensure CORS is set
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    
    return response


#generates an image url given a website 
@app.route('/find_image', methods=['POST'])
def random_image():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' field"}), 400

    url = data['url']
    headers = {'User-Agent': 'Mozilla/5.0'}  # Prevents being blocked
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all img tags on the page
        img_tags = soup.find_all('img')
        
        # Extract the src attribute of each image tag
        img_urls = [img['src'] for img in img_tags if 'src' in img.attrs]

        if not img_urls:
            return jsonify({"error": "No images found on this page."}), 404
        
        # Choose a random image URL
        random_img_url = random.choice(img_urls)
        
        return jsonify({"image_url": random_img_url})
    else:
        return jsonify({"error": f"Failed to fetch the webpage. Status Code: {response.status_code}"}), 400

@app.route('/select_link')
def select_link():

    with open('server/articles.txt', 'r') as file:
        articles = file.readlines()
    articles = [line.strip() for line in articles]

    with open('server/articleTitles.txt', 'r') as file:
        titles = file.readlines()
    titles = [line.strip() for line in titles]

    i = random.randint(0, len(articles)-1)
    print(i, len(articles), len(titles))
    return jsonify({"link" : articles[i], "title" : titles[i]})


@app.route('/get_status')
def get_status():
    # Sample data, but you could load it from a file or database as needed
  
  with open('server/data.json', 'r') as file:
    data = json.load(file)  # Parse the JSON data from the file


    # Returning the data as JSON
    return jsonify(data)



if __name__ == "__main__":
    app.run(debug=True)
