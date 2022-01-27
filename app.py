import re
import os
import enchant
import spacy
from flask import Flask, json,jsonify, request
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS, cross_origin
from spacy.tokens import Span
from spacy.matcher import PhraseMatcher
from spacy.language import Language
from scipy import spatial
from spacyFunctions import *
import smtplib
from datetime import datetime
from pickle4 import pickle

load_dotenv() 

# Defining spacy NLP Medium Model
nlp = spacy.load('en_core_web_md')
    
# Importing resource for indexing
pdffile = readTextFile('PlainConstitution0.txt', './resources/')
pdffile = pdffile.lower()

# Deserialization of NLP document
filename = 'ConstitutionDoc'
infile = open(filename,'rb')
doc = pickle.load(infile)
infile.close()
# End of serailization

# configuring regex matcher for the chapter titles
r_nlp = spacy.blank("en")
r_doc = r_nlp(pdffile)

# defining regex pattern for token enclosed in square braces
pattern = r"\[(.*?)\]" 
mwt_ents = []

# iterate over the document object while appending matched tokens
for match in re.finditer(pattern, r_doc.text):
    start, end = match.span()
    span = r_doc.char_span(start, end)
   
    if span is not None:
        mwt_ents.append((span.start, span.end, span.text))

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.secret_key = "secret_key"
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
mongo  = PyMongo(app)


@app.route('/', methods=['GET'])
@cross_origin()
def index():
    message = {
        'status': 200,
        'message': 'Welcome to the CADISE API :)c(:) '
    }

    resp = jsonify(message)
    resp.status_code = 200
    return resp
    
@app.route('/search', methods=['GET'])
@cross_origin()
def query_resource():
    # Define todays date
    today = datetime.now()

    # Extract search query String
    queryString = request.args.get('q')

    # Normalize query string
    normalText = normalizeText(queryString)

    similar_keywords = None

    # Get similar words base on query string
    similar_keywords = getSimilarWords(normalText, nlp)

    # Convert query string to nlp object
    refString = nlp(normalizeText(similar_keywords))

    # Split generated query string to get array representation of individual strings
    similar_keywords = normalizeText(similar_keywords).split(" ")
    
    # Define list stores
    searchResults = []
    positions = []
    searchSpans =[]
    similarityScores = []

    # Iteratively get matched phrases base on similar word list
    for word in similar_keywords:
        result = search_for_keyword(word, doc, nlp)
        searchResults += result["matched_text"]
        searchSpans += result["doc_text_span"]
        positions += result["start_positions"]
    
   

    # remove duplicate results in place
    uniqueList = remove_duplicates(searchResults, positions, searchSpans)

    # Access unduplicated lists using dictionary keys
    searchResults = uniqueList["a"]
    positions =  uniqueList["b"]
    searchSpans = uniqueList["c"]


    # Get semantic similarity scores for generated matched results
    for item in searchSpans:
        score = refString.similarity(item)
        similarityScores.append(score)

    # Obtain chaptes titles using document spans (start and end positions of text)
    title_list = []
    for item in positions:
        title_list.append(getTitle(mwt_ents,item))

    # print(f"{len(similarityScores)} and {len(searchResults)} and {len(title_list)}")

    rankedResults = sortRankedResults(similarityScores,searchResults,title_list )
    searchResults = rankedResults["results"]
    title_list = rankedResults["titles"]

    # print(rankedResults["control"])

    preparedResponse = []
    #  Iterating over all search results to order response object
    for i in range(len(searchResults)):
        title =  title_list[i]
        resultSent = searchResults[i]
        result = {
            "chapter": title[1:-1].capitalize(),
            "text": resultSent[:-1].capitalize()
        }

        preparedResponse.append(result)

    results = {
        "keywords": similar_keywords, 
               
        "results" : preparedResponse 
        
            }
    # Persist query log to database
    mongo.db.QueryLogs.insert_one({'queryString': queryString, 'queryDate':f'{today}', 'generatedKeywords':similar_keywords, 'totalResults': len(preparedResponse)})

    # Convert resp to JSON object
    resp = jsonify(results)
    resp.status_code = 200
    return resp

# Handle fetching of legal representatives list
@app.route('/get-legal', methods=['GET'])
@cross_origin()
def get_legal_list():
    legal_reps_list = mongo.db.LegalRepresentatives.find()
    resp = dumps(legal_reps_list)
    return resp

# Handle email delivery
@app.route('/contact-legal', methods=['POST'])
@cross_origin()
def send_email():
    content = request.json
    message=content['message']
    from_email=content['from_email']
    to_email = content['to_email']
    my_email = os.getenv('SYSTEM_EMAIL')
    my_password = os.getenv('SYSTEM_EMAIL_PASSWORD')

    # print(f"{to_email} {from_email}")
    if len(from_email) > 0 and len(to_email)> 0 and len(message) > 0:
        with smtplib.SMTP("smtp.mail.yahoo.com") as connection:
            connection.starttls()
            connection.login(user=my_email, password=my_password)
            connection.sendmail(
                from_addr=my_email,
                to_addrs=to_email,
                msg=f"Subject:CADISE SERVICE INQUIRY\n\n {from_email} says, \n{message}"
            )
        # print(content)
        resp = jsonify('Email Submitted')
        resp.status_code = 200
        return resp
    else:
        resp = jsonify('Message body incomplete')
        resp.status_code = 200
        return resp


@app.errorhandler(404)
@cross_origin()
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found ' + request.url
    }

    resp = jsonify(message)
    resp.status_code = 404
    return resp

PORT = os.getenv('PORT')
if __name__ :
    app.run(host='0.0.0.0', port=PORT, debug=False)
    
