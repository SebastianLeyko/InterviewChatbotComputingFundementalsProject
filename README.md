This project is made in collaboration with Sebastian Leyko, Johannes Sy, and Logan Greenwood as part of our Computing Fundementals class. The goal of this project is to have a fully functioning quizbot.

The goal of our project was to create an automatic quiz generator system that helps students or teachers to develop practice for any topic they need. We wanted to help students learn using more interactive materials than simple online worksheets. Our project:
-Converts PDF's to JSONs in a specific format
-Randomly generates 10 question quizzes using a user provided question bank
-grades the user inputs instantly (FRQ, MCQ, T/F)
-tracks the users performance
-Provides feedback for the user based off of keyword hits/misses for FRQ

HOW TO RUN PROJECT
1. Open bash and put in the following commands in order
2. git clone https://github.com/yourusername/quizbot.git
3. cd quizbot
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
Our Project was built through three major parts: 
1.We needed to create a question bank 
2.Then Build the PDF to JSON conversion 
3.Last Create the quiz and Grading system using flask 

Step by step: 
Question Bank 
For this section, we created a JSON file and then loaded all questions from this file. We then made the quiz pick 10 random questions from said file each time start quiz was pressed. After these were done we finalized the quiz by completing the grading system through Flask. 

Pseudocode: 
Load all questions from the question bank 

When user hits Start Quiz 
Chose 10 random questions 
Create a quiz ID 
Store the list of picked question IDs 
Send questions to website 

PDF to JSON 
For this part, we created a coverter to all the user (teacher or student) to upload a pdf, the code then extracts the text from the pdf and breakes it into different question blocks. Last we saved all these question into a question_bank.json file. 

Pseudocode: 
When user uploads a PDF 
Read text in pdf 
Split the text into sections 
For each section: 
Find question type TF, MCQ, FRQ 
Find question prompt 
Find keywords/answer 
Save it in json as a question 
Update question bank file 

Quiz and Time 
For our quiz section we rendered the 10 selected questions onto the website, started tracking time when the user clicked start quiz and when the user begins each question, and collected all the responses and time spent. 

Pseudocode: 
Load Quiz (start quiz button) 
Show each question on the website 
When user clicks on answer or types  
Start timer 
When user clicks submit 
For each question 
record answers 
record time spent 
Send everything to backend 

Grading 
For the last part our grading system compared the users inputs to the rubric, checked for exact matches and keywords, returns feedback + keywords missed, and logs results into a file to keep a record. 

Pseudocode: 
For each answer 
Find the question in the question bank 
If question is T/F 
check if answer matches 
If question is MCQ 
check if answer matches 
If question FRQ 
Count how many keywords are hit 
Score based on the keyword percentage 
Save score and feedback 
Add to total score 
Save total score and time into a json log file 
Return the results to the webpage in results 


RESULTS
<img src="Overleaf & Excel/1.png">
This Screenshot above shows how the website looks when you first open it up, before inputting any pdfs or clicking start quiz. Our homepage includes a dropdown menu to select whether you are uploading a question bank or rubric, a file selector, an upload button, and the start quiz button. This shows that our system initializes properly and is able to load on peoples computers. 

<img src="Overleaf & Excel/2.png">
Here we see the upload confirmation that is shown after you upload a pdf. In this example, I uploaded a 50-question-long PDF, and as you can see, it shows the correct count of questions and tells us the status of the import. This confirms that our pdf to json converter is functioning through the webpage with no errors. 

<img src="Overleaf & Excel/3.png">
Above we have the upload confirmation for the rubric which just shows the status of the rubric. As said before this shows that our pdf to json converter is functioning as expected. 

<img src="Overleaf & Excel/4.png">
Here you can see the keyword bank that is generated from the free response questions in the quiz. Since this generates correctly and has the correct keywords this proves that our keyword logic is functioning and that the FRQ data is being processed correctly. 

<img src="Overleaf & Excel/5.png">
Above is a screenshot of what the webpage looks like after you hit start quiz. This page includes the 10 randomly generated questions, the class performance for those questions, the FRQ boxes, and the FRQ keywords. This shows that our random sampling of questions works, our class performance tracking is functioning, our page rendered correctly with all types of questions displayed, and the UI is updating accurately. 

<img src="Overleaf & Excel/6.png">
Here is a close up of a question, so you can see what the class performance tracking looks like. 

 <img src="Overleaf & Excel/7.png">
Here is the full results table that you recieve after submitting your quiz. This table should hold information such as your score per question, total score, type of question, time taken total, time taken per question, feedback, keywords (hits and misses), and color coded for answers. As you can see all of this data is correctly displayed in the table which means that our grading module is functioning as expected. 

<img src="Overleaf & Excel/8.png">
Above is the raw output that the backend code gives us in a json file. Here you can see the ID of the questions, keywords, points, time, and type of question. This confirms that our API is returning structured data that can easily be transformed into the nice looking table prior. It also means that all fields that are required for the UI rendering were present and the json file matches the table above. This shows that our front end and back end are working together to keep the quiz functioning. 
 

  







