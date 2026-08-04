import os
import joblib
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline

# Ensure models directory exists
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

CLASSIFIER_PATH = os.path.join(MODELS_DIR, 'intent_classifier.pkl')
VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')

print("Generating synthetic academic dataset...")

# Generate a large robust dataset for academic queries
dataset = [
    # download (30)
    ("download the pdf", "download"), ("get the document", "download"), ("give me the pdf", "download"), 
    ("download this course material", "download"), ("where can I download", "download"),
    ("download slides", "download"), ("get lecture notes pdf", "download"), ("download pyq", "download"),
    ("save document", "download"), ("offline copy", "download"), ("download syllabus", "download"),
    ("can you download this", "download"), ("download file", "download"), ("pdf download", "download"),
    ("get the offline pdf", "download"), ("download chapter 1", "download"), ("download chapter 2", "download"),
    ("download the textbook", "download"), ("i want to download this", "download"), ("give me a download link", "download"),
    ("link to download", "download"), ("download the assignment", "download"), ("download the solutions", "download"),
    ("download the past year questions", "download"), ("how to download", "download"), ("download notes", "download"),
    ("download the entire folder", "download"), ("get pdf version", "download"), ("download printable version", "download"),
    
    # faculty_lookup (30)
    ("who teaches this course", "faculty_lookup"), ("professor details", "faculty_lookup"), 
    ("who is the instructor", "faculty_lookup"), ("faculty for CS101", "faculty_lookup"),
    ("who teaches CS101", "faculty_lookup"), ("what is the professor's email", "faculty_lookup"),
    ("ta details", "faculty_lookup"), ("teaching assistant", "faculty_lookup"),
    ("who are the TAs", "faculty_lookup"), ("contact instructor", "faculty_lookup"),
    ("who is taking this course", "faculty_lookup"), ("faculty in charge", "faculty_lookup"),
    ("course coordinator", "faculty_lookup"), ("who teaches machine learning", "faculty_lookup"),
    ("professor office hours", "faculty_lookup"), ("instructor name", "faculty_lookup"),
    ("who is the prof", "faculty_lookup"), ("faculty contact", "faculty_lookup"),
    ("prof email id", "faculty_lookup"), ("instructor cabin", "faculty_lookup"),
    ("who is the faculty", "faculty_lookup"), ("tell me about the professor", "faculty_lookup"),
    ("faculty research areas", "faculty_lookup"), ("who is teaching next semester", "faculty_lookup"),
    ("list of instructors", "faculty_lookup"), ("who teaches physics", "faculty_lookup"),
    
    # list_documents (30)
    ("show all documents", "list_documents"), ("list pyqs", "list_documents"), 
    ("what documents are available", "list_documents"), ("uploaded materials", "list_documents"),
    ("list all files", "list_documents"), ("show me the notes", "list_documents"),
    ("what files are uploaded", "list_documents"), ("list course materials", "list_documents"),
    ("available resources", "list_documents"), ("list assignments", "list_documents"),
    ("show all slides", "list_documents"), ("list lectures", "list_documents"),
    ("documents available for CS101", "list_documents"), ("list pdfs", "list_documents"),
    ("what are the uploaded pyqs", "list_documents"), ("show me past papers", "list_documents"),
    ("list all past year questions", "list_documents"), ("show uploaded documents", "list_documents"),
    ("list the handouts", "list_documents"), ("what handouts are there", "list_documents"),
    ("list of reference books", "list_documents"), ("documents for unit 1", "list_documents"),
    ("show me all materials", "list_documents"), ("list the reading materials", "list_documents"),
    
    # list_courses (25)
    ("what courses are there", "list_courses"), ("available courses", "list_courses"),
    ("list all courses", "list_courses"), ("courses offered in autumn", "list_courses"),
    ("show me the courses", "list_courses"), ("what courses can I take", "list_courses"),
    ("list of electives", "list_courses"), ("courses in computer science", "list_courses"),
    ("show courses for department", "list_courses"), ("what is offered this semester", "list_courses"),
    ("list department courses", "list_courses"), ("courses available", "list_courses"),
    ("show me electives", "list_courses"), ("list all btech courses", "list_courses"),
    ("courses offered by EE", "list_courses"), ("what courses are taught", "list_courses"),
    ("list breadth courses", "list_courses"), ("show hss electives", "list_courses"),
    ("list core courses", "list_courses"), ("courses in spring semester", "list_courses"),
    
    # prerequisites (25)
    ("prerequisites for CS101", "prerequisites"), ("what should I know before", "prerequisites"),
    ("do I need to take", "prerequisites"), ("is there a prerequisite", "prerequisites"),
    ("what are the prereqs", "prerequisites"), ("required before taking", "prerequisites"),
    ("foundation for this course", "prerequisites"), ("what to study before", "prerequisites"),
    ("prereq for machine learning", "prerequisites"), ("background required", "prerequisites"),
    ("what is the prerequisite", "prerequisites"), ("requirements to enroll", "prerequisites"),
    ("do I need programming for this", "prerequisites"), ("prior knowledge needed", "prerequisites"),
    ("prerequisites for data structures", "prerequisites"), ("what courses to take first", "prerequisites"),
    ("is calculus required", "prerequisites"), ("what should i complete before", "prerequisites"),
    ("eligibility for this course", "prerequisites"), ("prerequisites", "prerequisites"),
    
    # compare (25)
    ("difference between x and y", "compare"), ("compare two things", "compare"),
    ("how is this different from", "compare"), ("vs", "compare"), ("versus", "compare"),
    ("distinction between", "compare"), ("compare TCP and UDP", "compare"),
    ("what is the difference between", "compare"), ("how does A compare to B", "compare"),
    ("contrast A and B", "compare"), ("similarities and differences", "compare"),
    ("compare BFS and DFS", "compare"), ("difference between array and list", "compare"),
    ("what differentiates", "compare"), ("which is better", "compare"),
    ("compare python and java", "compare"), ("differentiate between", "compare"),
    ("tell me the difference", "compare"), ("how to distinguish", "compare"),
    ("compare and contrast", "compare"), ("comparison of", "compare"),
    
    # relationship (20)
    ("how is this related", "relationship"), ("connection between", "relationship"),
    ("relationship between", "relationship"), ("link between", "relationship"),
    ("how does this connect to", "relationship"), ("are they related", "relationship"),
    ("what is the relation", "relationship"), ("connection of A to B", "relationship"),
    ("how do they link", "relationship"), ("relation between force and mass", "relationship"),
    ("how does entropy relate to", "relationship"), ("is there a connection", "relationship"),
    ("relationship of", "relationship"), ("how are they linked", "relationship"),
    ("correlation between", "relationship"), ("how does this tie into", "relationship"),
    ("what connects them", "relationship"), ("show the relation", "relationship"),
    
    # figure_search (25)
    ("show me the image", "figure_search"), ("give me figure 1", "figure_search"),
    ("show figure 3", "figure_search"), ("get figure", "figure_search"),
    ("image of the architecture", "figure_search"), ("diagram for", "figure_search"),
    ("plot of the graph", "figure_search"), ("chart showing", "figure_search"),
    ("illustration of", "figure_search"), ("picture of", "figure_search"),
    ("visual representation", "figure_search"), ("show me figure 2", "figure_search"),
    ("give me the figure", "figure_search"), ("show the diagram", "figure_search"),
    ("fetch the image", "figure_search"), ("where is the figure", "figure_search"),
    ("show the block diagram", "figure_search"), ("plot the data", "figure_search"),
    ("show me the chart", "figure_search"), ("display the image", "figure_search"),
    
    # table_search (20)
    ("from the table", "table_search"), ("data row", "table_search"),
    ("column 3", "table_search"), ("what is in the table", "table_search"),
    ("show me table 1", "table_search"), ("fetch table 2", "table_search"),
    ("table containing", "table_search"), ("data in table", "table_search"),
    ("look at the table", "table_search"), ("table showing", "table_search"),
    ("get table data", "table_search"), ("extract table", "table_search"),
    ("show the table", "table_search"), ("table for comparison", "table_search"),
    ("what does the table say", "table_search"), ("row 5 of table", "table_search"),
    
    # structural_search (20)
    ("chapter 2", "structural_search"), ("under the heading", "structural_search"),
    ("section 3.1", "structural_search"), ("in chapter 5", "structural_search"),
    ("heading Introduction", "structural_search"), ("under the topic", "structural_search"),
    ("what does chapter 1 say", "structural_search"), ("section about", "structural_search"),
    ("in the conclusion section", "structural_search"), ("chapter 4 details", "structural_search"),
    ("look in section 2", "structural_search"), ("heading of", "structural_search"),
    ("read chapter 3", "structural_search"), ("what is in section 4", "structural_search"),
    ("subheading", "structural_search"), ("topic heading", "structural_search"),
    
    # concept_search (25)
    ("syllabus", "concept_search"), ("course content", "concept_search"),
    ("what topics are covered", "concept_search"), ("does it cover", "concept_search"),
    ("what is in the syllabus", "concept_search"), ("topics included", "concept_search"),
    ("curriculum", "concept_search"), ("what will we learn", "concept_search"),
    ("does this course teach", "concept_search"), ("is machine learning covered", "concept_search"),
    ("list the topics", "concept_search"), ("show syllabus", "concept_search"),
    ("course outline", "concept_search"), ("topics in midsem", "concept_search"),
    ("what is the syllabus for", "concept_search"), ("content of course", "concept_search"),
    ("topics taught", "concept_search"), ("what concepts", "concept_search"),
    
    # topic_explain (30)
    ("explain how", "topic_explain"), ("describe this", "topic_explain"),
    ("what is", "topic_explain"), ("how does it work", "topic_explain"),
    ("explain the concept of", "topic_explain"), ("what is the meaning of", "topic_explain"),
    ("describe the process", "topic_explain"), ("explain the theorem", "topic_explain"),
    ("how does the algorithm work", "topic_explain"), ("explain TCP/IP", "topic_explain"),
    ("what is polymorphism", "topic_explain"), ("describe mitosis", "topic_explain"),
    ("explain the derivation", "topic_explain"), ("give an explanation", "topic_explain"),
    ("can you explain", "topic_explain"), ("elaborate on", "topic_explain"),
    ("how do you define", "topic_explain"), ("what do you mean by", "topic_explain"),
    ("explain with example", "topic_explain"), ("describe in detail", "topic_explain"),
    ("what exactly is", "topic_explain"), ("how does recursion work", "topic_explain"),
    
    # semantic_search (25)
    ("find notes on", "semantic_search"), ("search for", "semantic_search"),
    ("where is", "semantic_search"), ("look up", "semantic_search"),
    ("search", "semantic_search"), ("find information about", "semantic_search"),
    ("where can I find", "semantic_search"), ("search the documents for", "semantic_search"),
    ("find pyq about", "semantic_search"), ("search notes for", "semantic_search"),
    ("find mention of", "semantic_search"), ("where is it mentioned", "semantic_search"),
    ("search the slides", "semantic_search"), ("find the formula for", "semantic_search"),
    ("search the text for", "semantic_search"), ("find details on", "semantic_search"),
    ("search knowledge base", "semantic_search"), ("find references to", "semantic_search"),
    
    # general_qa (20)
    ("hello", "general_qa"), ("what is your name", "general_qa"),
    ("who are you", "general_qa"), ("how are you", "general_qa"),
    ("good morning", "general_qa"), ("hi", "general_qa"),
    ("what can you do", "general_qa"), ("help me", "general_qa"),
    ("what are your capabilities", "general_qa"), ("are you an AI", "general_qa"),
    ("thanks", "general_qa"), ("thank you", "general_qa"),
    ("goodbye", "general_qa"), ("bye", "general_qa"),
    ("who created you", "general_qa"), ("how does this chat work", "general_qa"),
    ("test", "general_qa"), ("ping", "general_qa")
]

X_train = [item[0] for item in dataset]
y_train = [item[1] for item in dataset]

print(f"Dataset size: {len(dataset)} queries across {len(set(y_train))} intents.")
print("Training TF-IDF Vectorizer...")

vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)

print("Training SVM Classifier...")
clf = SVC(kernel='linear', probability=True)
clf.fit(X_train_vec, y_train)

# Save models
print(f"Saving vectorizer to {VECTORIZER_PATH}")
joblib.dump(vectorizer, VECTORIZER_PATH)

print(f"Saving classifier to {CLASSIFIER_PATH}")
joblib.dump(clf, CLASSIFIER_PATH)

print("Training complete! The backend will now load these models successfully.")
