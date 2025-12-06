This project is made in collaboration with Sebastian Leyko, Johannes Sy, and Logan Greenwood as part of our Computing Fundementals class. The goal of this project is to have a fully functioning quizbot.

The goal of our project was to create an automatic quiz generator system that helps students or teachers to develop practice for any topic they need. We wanted to help students learn using more interactive materials than simple online worksheets. Our project:
-Converts PDF's to JSONs in a specific format
-Randomly generates 10 question quizzes using a user provided question bank
-grades the user inputs instantly (FRQ, MCQ, T/F)
-tracks the users performance
-Provides feedback for the user based off of keyword hits/misses for FRQ

HOW TO RUN PROJECT
1. Open bash and put in the following commands in order
2. git clone https://github.com/yourusername/quiz-bot.git
3. cd quiz-bot
4. python -m venv venv
5. venv\Scripts\activate  ****For Windows
6. source venv/bin/activate   ***For Mac
7. pip install -r requirements.txt
8. python app.py
9. then you can access the website on the ip address it provides
10. OPTIONAL: I used ngrok to run the program on a seperate domain that allows other computers to use the webpage you can do this by following this link https://ngrok.com/

DEPENDENCIES
-Flask   -used for backend web framework
-pdfplumber   -used to extract text from the pdfs
-uuid   -gave the unique quiz session ID
-json   -Used for storing data
-pathlib   -File paths


  METHODOLOGY

  RESULTS

  







