from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import logging
import re

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)  # Enable CORS to allow requests from your Chrome extension
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

def extract_json_from_text(text):
    # Use a regular expression to extract JSON data from the output
    match = re.search(r'{.*}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

def analyze_with_ollama(policy_text):
    # Define the prompt for guiding the LLM
    prompt = """Provide a structured JSON output with individual ratings and explanations for each of the following parameters, as well as a final rating and explanation:
    {
        "ratings": {
            "Data Collection": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            },
            "Data Usage": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            },
            "Data Sharing with Third Parties": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            },
            "Data Selling to Third Parties": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            },
            "Opt-Out Options for Data Sharing": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            },
            "Data Security": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            },
            "Data Deletion": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            },
            "Policy Clarity": {
                "rating": <rating out of 5>,
                "explanation": <explanation for the rating>
            }
        },
        "final_rating": {
            "rating": <overall rating out of 5>,
            "explanation": <explanation for the final rating>
        }
    }
    """

    # Combine the prompt with the policy text
    full_text = prompt + "\n" + policy_text

    # Run the command to analyze with Ollama
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=full_text,
        capture_output=True,
        text=True
    )

    # Log the full output from Ollama for debugging
    logging.info(f"Ollama Output: {result.stdout}")

    # Check if the command executed successfully
    if result.returncode != 0:
        logging.error(f"Error running Ollama: {result.stderr}")
        return {"error": f"Error running Ollama: {result.stderr}"}

    # Attempt to extract and parse the JSON response
    analysis = extract_json_from_text(result.stdout)
    if analysis:
        # Restructure the data to make it clearer
        structured_response = {
            "ratings": [
                {
                    "parameter": "Data Collection",
                    "rating": analysis["ratings"]["Data Collection"]["rating"],
                    "explanation": analysis["ratings"]["Data Collection"]["explanation"]
                },
                {
                    "parameter": "Data Usage",
                    "rating": analysis["ratings"]["Data Usage"]["rating"],
                    "explanation": analysis["ratings"]["Data Usage"]["explanation"]
                },
                {
                    "parameter": "Data Sharing with Third Parties",
                    "rating": analysis["ratings"]["Data Sharing with Third Parties"]["rating"],
                    "explanation": analysis["ratings"]["Data Sharing with Third Parties"]["explanation"]
                },
                {
                    "parameter": "Data Selling to Third Parties",
                    "rating": analysis["ratings"]["Data Selling to Third Parties"]["rating"],
                    "explanation": analysis["ratings"]["Data Selling to Third Parties"]["explanation"]
                },
                {
                    "parameter": "Opt-Out Options for Data Sharing",
                    "rating": analysis["ratings"]["Opt-Out Options for Data Sharing"]["rating"],
                    "explanation": analysis["ratings"]["Opt-Out Options for Data Sharing"]["explanation"]
                },
                {
                    "parameter": "Data Security",
                    "rating": analysis["ratings"]["Data Security"]["rating"],
                    "explanation": analysis["ratings"]["Data Security"]["explanation"]
                },
                {
                    "parameter": "Data Deletion",
                    "rating": analysis["ratings"]["Data Deletion"]["rating"],
                    "explanation": analysis["ratings"]["Data Deletion"]["explanation"]
                },
                {
                    "parameter": "Policy Clarity",
                    "rating": analysis["ratings"]["Policy Clarity"]["rating"],
                    "explanation": analysis["ratings"]["Policy Clarity"]["explanation"]
                }
            ],
            "final_rating": {
                "rating": analysis["final_rating"]["rating"],
                "explanation": analysis["final_rating"]["explanation"]
            }
        }
        return structured_response

    # If JSON extraction fails, log an error
    logging.error(f"Unexpected non-JSON output from Ollama: {result.stdout}")
    return {"error": "Failed to parse JSON output from Ollama"}

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    policy_text = data.get("policy_text", "")

    if not policy_text:
        return jsonify({"error": "No policy text provided"}), 400

    result = analyze_with_ollama(policy_text)

    # Check if there was an error in the analysis
    if "error" in result:
        return jsonify(result), 500

    logging.info(f"Backend response: {result}")
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=8000, debug=True)
