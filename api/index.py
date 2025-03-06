import os
import subprocess
import logging
import tempfile
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConvertRequest(BaseModel):
    url: str

@app.get("/")
def home():
    """Test route to check if the server is running."""
    return {"message": "✅ Server is running on Vercel!"}

@app.post("/convert")
def convert(data: ConvertRequest):
    """Convert a website URL to an unsigned APK."""
    website_url = data.url

    if not website_url:
        raise HTTPException(status_code=400, detail="Missing website URL")

    logging.debug(f"Received URL: {website_url}")

    try:
        apk_path = generate_apk(website_url, signed=False)  # Generate an unsigned APK
        logging.debug(f"APK generated at path: {apk_path}")
        return {"message": "APK generated successfully", "path": apk_path}
    except Exception as e:
        logging.error(f"❌ Error generating APK: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate APK: {e}")

def generate_apk(website_url, signed=False):
    """
    Generate an APK from a website URL using apktool.
    
    Args:
        website_url (str): The URL of the website to convert to an APK.
        signed (bool): Whether to sign the APK or not.
    
    Returns:
        str: The path to the generated APK file.
    
    Raises:
        Exception: If APK generation fails.
    """
    output_apk = "web_app_converter.apk"
    apktool_path = os.path.join("tools", "apktool.jar")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy the input-folder contents to the temporary directory
        input_folder = os.path.join(temp_dir, "input-folder")
        shutil.copytree("input-folder", input_folder)
        
        # Ensure the necessary directories and files exist
        main_activity_dir = os.path.join(input_folder, "src", "com", "example", "app")
        main_activity_path = os.path.join(main_activity_dir, "MainActivity.java")
        
        if not os.path.exists(main_activity_dir):
            os.makedirs(main_activity_dir)
        
        if not os.path.exists(main_activity_path):
            with open(main_activity_path, "w") as file:
                file.write("""
                package com.example.app;

                import android.os.Bundle;
                import android.webkit.WebView;
                import androidx.appcompat.app.AppCompatActivity;

                public class MainActivity extends AppCompatActivity {
                    @Override
                    protected void onCreate(Bundle savedInstanceState) {
                        super.onCreate(savedInstanceState);
                        setContentView(R.layout.activity_main);

                        WebView webView = findViewById(R.id.webview);
                        webView.loadUrl("http://example.com");  // Replace with the actual URL
                    }
                }
                """)
        
        # Update the MainActivity.java file with the provided URL
        with open(main_activity_path, "r") as file:
            content = file.read()
        
        content = content.replace("http://example.com", website_url)
        
        with open(main_activity_path, "w") as file:
            file.write(content)
        
        # Command to build the APK
        command = f"java -jar {apktool_path} b {input_folder} -o {output_apk}"
        
        try:
            # Log the command being executed
            logging.debug(f"Running command: {command}")
            
            # Run the apktool command
            logging.info(f"Generating APK for website: {website_url}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            # Log the result of the command
            logging.debug(f"Command stdout: {result.stdout}")
            logging.debug(f"Command stderr: {result.stderr}")

            if result.returncode == 0:
                logging.info(f"APK generated successfully: {output_apk}")
                return output_apk
            else:
                logging.error(f"APK generation failed: {result.stderr}")
                raise Exception(f"APK Generation Failed: {result.stderr}")
        except Exception as e:
            logging.error(f"Error during APK generation: {e}")
            raise Exception(f"APK Generation Failed: {e}")