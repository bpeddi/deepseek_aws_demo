# Use an official Python image as a base
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the required files
COPY chatbot.py requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the chatbot
CMD ["streamlit", "run", "chatbot.py", "--server.port=8501", "--server.address=0.0.0.0"]