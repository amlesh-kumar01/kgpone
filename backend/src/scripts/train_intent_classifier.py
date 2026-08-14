"""
Trains a TF-IDF + LinearSVC intent classifier for the RAG query planner.
Generates synthetic training data from the 11 intent categories and saves
the trained model + vectorizer as pickle files.

Usage:
    uv run python -m src.scripts.train_intent_classifier
"""

import os
import logging
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_intent_classifier")

# ─── Synthetic Training Data ────────────────────────────────────────────────
# Each intent has ~30-50 example queries to ensure decent coverage.

TRAINING_DATA = {
    "download": [
        "download lecture 5 pdf",
        "get the syllabus pdf",
        "download assignment 3",
        "can you give me the pdf for lecture 12",
        "download the notes for week 4",
        "get me the PYQ paper",
        "download previous year question paper",
        "give me the course handout pdf",
        "I need the pdf for tutorial 6",
        "download the slides for module 3",
        "get lecture notes pdf",
        "download reference material",
        "where can I download the textbook",
        "give me the solution pdf",
        "download exam paper 2024",
        "get the lab manual pdf",
        "download class notes",
        "I want to download the presentation slides",
        "share the pdf link for lecture 8",
        "download the formula sheet",
        "get me the reading material pdf",
        "download tutorial sheet 2",
        "can I get the pdf of this document",
        "I need to download the project report template",
        "download the grading rubric",
    ],
    "faculty_lookup": [
        "who teaches CS60001",
        "professor's email for operating systems",
        "who is the instructor for algorithms",
        "faculty details for CS101",
        "who teaches this course",
        "what is the professor's office hours",
        "contact details of the instructor",
        "who is teaching data structures this semester",
        "professor email address",
        "faculty information for machine learning",
        "who is the TA for this course",
        "instructor name for CS201",
        "which professor handles the lab",
        "email of the course coordinator",
        "who is the head of CSE org_unit",
        "faculty members teaching AI",
        "professor's contact number",
        "who conducts the tutorial sessions",
        "TA office hours for CS301",
        "instructor details for compilers",
        "which faculty teaches database systems",
        "who is the examiner for this course",
        "professor profile for networks",
    ],
    "list_documents": [
        "show all PYQs for CS101",
        "list my uploaded notes",
        "what documents are available for this course",
        "show all lecture slides",
        "list the uploaded materials",
        "what notes have been uploaded",
        "show previous year papers",
        "give all available documents",
        "list all assignments",
        "what study materials are available",
        "show me all the resources",
        "list tutorial sheets",
        "what papers are in the database",
        "show available reference materials",
        "list all uploaded files for OS",
        "what documents exist for algorithms",
        "show me the document library",
        "available materials for this offering",
        "show all lab sheets",
        "list course materials",
        "what files have been shared",
        "show uploaded documents for data structures",
    ],
    "list_courses": [
        "what courses does CSE offer",
        "list all available courses",
        "show courses in computer science org_unit",
        "what subjects are offered this semester",
        "list elective courses",
        "available courses for spring 2025",
        "show me all courses in ECE",
        "what courses can I take",
        "list courses with 3 credits",
        "show org_unit course catalog",
        "what are the mandatory courses",
        "list all foundation courses",
        "available subjects in mathematics",
        "show me the course list",
        "what courses are running this year",
        "list all postgraduate courses",
        "courses offered by mechanical engineering",
        "show available electives",
        "what specialization courses exist",
        "list honors courses",
    ],
    "prerequisites": [
        "what are the prerequisites for OS",
        "do I need math for machine learning",
        "prerequisite courses for algorithms",
        "what should I study before taking AI",
        "prerequisites for database systems",
        "what courses do I need before compilers",
        "is linear algebra required for ML",
        "prerequisite chain for advanced algorithms",
        "what foundation do I need for networks",
        "do I need probability for data science",
        "prerequisite requirements for CS601",
        "what must I complete before this course",
        "is data structures a prerequisite",
        "required courses before taking operating systems",
        "what prior knowledge is needed for computer graphics",
        "prerequisites for distributed systems",
        "do I need OOP before design patterns",
        "what is the prerequisite tree for this subject",
        "foundation courses needed for cryptography",
        "is discrete math required for algorithms",
        "what courses lead to machine learning",
        "prerequisite map for artificial intelligence",
    ],
    "topic_explain": [
        "explain attention mechanism",
        "what is a CNN",
        "explain how backpropagation works",
        "what is dynamic programming",
        "explain the concept of virtual memory",
        "what are semaphores",
        "explain binary search tree",
        "what is a hash table",
        "explain gradient descent",
        "what is polymorphism",
        "explain deadlock in operating systems",
        "what is normalization in databases",
        "explain the OSI model",
        "what is a stack data structure",
        "explain recursion",
        "what is object oriented programming",
        "explain how transformers work",
        "what is a linked list",
        "explain the concept of threading",
        "what is encapsulation",
        "explain page replacement algorithms",
        "what is a B-tree",
        "explain the concept of inheritance",
        "what is a graph data structure",
        "explain the dining philosophers problem",
        "what is process scheduling",
        "explain convolution in neural networks",
        "what are design patterns",
        "explain TCP three-way handshake",
        "what is a priority queue",
    ],
    "compare": [
        "compare CNN and ViT",
        "difference between DFS and BFS",
        "compare stack and queue",
        "what is the difference between TCP and UDP",
        "compare merge sort and quick sort",
        "difference between process and thread",
        "compare relational and NoSQL databases",
        "what is the difference between abstraction and encapsulation",
        "compare supervised and unsupervised learning",
        "difference between array and linked list",
        "compare REST and GraphQL",
        "what is the difference between compiler and interpreter",
        "compare binary tree and binary search tree",
        "difference between paging and segmentation",
        "compare LSTM and GRU",
        "what is the difference between HTTP and HTTPS",
        "compare greedy and dynamic programming",
        "difference between mutex and semaphore",
        "compare IPv4 and IPv6",
        "what is the difference between overloading and overriding",
        "how does RNN differ from transformer",
        "compare breadth first and depth first traversal",
        "distinction between concurrency and parallelism",
        "compare monolithic and microservices architecture",
    ],
    "concept_search": [
        "what topics does CS20006 cover",
        "what is in chapter 2 of algorithms",
        "topics covered in the syllabus",
        "what concepts are taught in week 5",
        "course content for database systems",
        "what topics are in module 3",
        "syllabus coverage for machine learning",
        "what does this course cover",
        "topics in the operating systems curriculum",
        "what concepts are in the midterm syllabus",
        "course outline for computer networks",
        "what is taught in lecture 7",
        "topics for the final exam",
        "what algorithms are covered in this course",
        "content of the data structures syllabus",
        "what units are in the course",
        "topics in neural networks module",
        "what is the scope of this subject",
        "course topics for software engineering",
        "what chapters are included in the exam",
    ],
    "semantic_search": [
        "notes on dynamic programming",
        "where did the professor mention arrays",
        "find content about gradient descent",
        "search for deadlock avoidance techniques",
        "where is binary tree traversal discussed",
        "find relevant material on neural networks",
        "search notes for recursion examples",
        "where are sorting algorithms explained",
        "find content about TCP protocol",
        "search for information on page tables",
        "where is the discussion on normalization",
        "find notes about object oriented design",
        "search for examples of inheritance",
        "where does the textbook cover hashing",
        "find material on graph algorithms",
        "search for process synchronization content",
        "where is virtual memory explained",
        "find relevant sections on linked lists",
        "search for matrix multiplication algorithms",
        "find content about operating system scheduling",
        "search notes for database indexing",
        "where are pointers discussed in the notes",
        "find examples of dynamic programming problems",
    ],
    "relationship": [
        "how is DFS related to BFS",
        "connection between A and B",
        "how does sorting relate to searching",
        "what connects neural networks and deep learning",
        "relationship between classes and objects",
        "how are stacks and recursion connected",
        "link between probability and machine learning",
        "how does OS relate to computer architecture",
        "connection between graphs and trees",
        "how are databases and SQL related",
        "relationship between algorithms and data structures",
        "how does linear algebra connect to ML",
        "link between TCP and IP protocols",
        "how are threads related to processes",
        "connection between hashing and hash tables",
        "how does compiler design relate to automata theory",
        "what connects dynamic programming and recursion",
        "how are encryption and decryption related",
        "relationship between normalization and database design",
        "link between operating systems and networks",
    ],
    "general_qa": [
        "explain backpropagation with formulas",
        "how to solve this recurrence relation",
        "solve this problem step by step",
        "give me the formula for complexity analysis",
        "how to implement quicksort in Python",
        "write the pseudocode for Dijkstra's algorithm",
        "prove that this algorithm is O(n log n)",
        "derive the time complexity",
        "show the proof for this theorem",
        "calculate the optimal solution",
        "how to approach this assignment problem",
        "explain this code snippet",
        "what is the output of this program",
        "help me understand this derivation",
        "solve this dynamic programming problem",
        "explain the mathematical proof",
        "how to debug this error",
        "give a numerical example of this algorithm",
        "trace through this recursive function",
        "what are the steps to solve this",
        "explain how to optimize this query",
        "walk me through this solution",
        "how do I implement this data structure",
        "what is the best approach for this problem",
        "help me with this homework question",
    ],
}


def generate_training_data():
    """Flatten training data into (texts, labels) lists."""
    texts = []
    labels = []
    for intent, examples in TRAINING_DATA.items():
        for example in examples:
            texts.append(example)
            labels.append(intent)
    return texts, labels


def train_and_save():
    """Train TF-IDF + LinearSVC pipeline, evaluate, and save artifacts."""
    texts, labels = generate_training_data()
    logger.info(f"Total training samples: {len(texts)} across {len(TRAINING_DATA)} intents")

    # Split for evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # Train TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
        sublinear_tf=True,
        min_df=1,
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Train LinearSVC with probability calibration (CalibratedClassifierCV wraps SVC to give predict_proba)
    base_svc = LinearSVC(max_iter=5000, class_weight="balanced", C=1.0)
    classifier = CalibratedClassifierCV(base_svc, cv=3)
    classifier.fit(X_train_tfidf, y_train)

    # Evaluate
    y_pred = classifier.predict(X_test_tfidf)
    report = classification_report(y_test, y_pred)
    logger.info(f"\nClassification Report:\n{report}")

    # Save artifacts
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    os.makedirs(models_dir, exist_ok=True)

    vectorizer_path = os.path.join(models_dir, "tfidf_vectorizer.pkl")
    classifier_path = os.path.join(models_dir, "intent_classifier.pkl")

    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(classifier, classifier_path)

    logger.info(f"Saved vectorizer to: {vectorizer_path}")
    logger.info(f"Saved classifier to: {classifier_path}")
    logger.info(f"Vectorizer file size: {os.path.getsize(vectorizer_path) / 1024:.1f} KB")
    logger.info(f"Classifier file size: {os.path.getsize(classifier_path) / 1024:.1f} KB")

    return vectorizer_path, classifier_path


if __name__ == "__main__":
    train_and_save()
