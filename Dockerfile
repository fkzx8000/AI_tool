# השתמש בבסיס תמונה של Python
FROM python:3.12.3

# הגדר את תיקיית העבודה
WORKDIR /app

# העתק את קובצי הדרישות לתוך התמונה
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# העתק את שאר קבצי הפרויקט לתוך התמונה
COPY . .
# Make the script executable
RUN chmod +x /app/api_key_test.py
# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Expose port 5000 to the outside world
EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=localhost","/app/api_key_test.py"]
