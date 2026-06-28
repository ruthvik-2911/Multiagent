from neo4j import GraphDatabase
from backend.services.activity_service import log_activity

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

def run_query(query, parameters=None):
    with driver.session() as session:
        session.run(query, parameters or {})

def create_document(profile):
    query = """
    MERGE (d:Document {file_name:$file_name})
    SET d.display_name=$display_name,
        d.summary=$summary,
        d.folder=$folder,
        d.file_type=$file_type
    """
    run_query(query, profile)
    log_activity("Neo4j Updated", profile.get("file_name", "unknown"))

def delete_document(file_name):
    query = """
    MATCH (d:Document {file_name:$file_name})
    OPTIONAL MATCH (d)-[r:HAS_KEYWORD]->(k:Keyword)
    DELETE r, d
    WITH k
    WHERE k IS NOT NULL AND NOT (k)<-[:HAS_KEYWORD]-()
    DELETE k
    """
    run_query(query, {"file_name": file_name})
    log_activity("Neo4j Deleted", file_name)

def create_keyword(keyword):
    query = """
    MERGE (k:Keyword {name:$keyword})
    """
    run_query(query, {"keyword": keyword})

def create_relationship(file_name, keyword):
    query = """
    MATCH (d:Document {file_name:$file_name})
    MATCH (k:Keyword {name:$keyword})
    MERGE (d)-[:HAS_KEYWORD]->(k)
    """
    run_query(query, {
        "file_name": file_name,
        "keyword": keyword
    })

def search_keywords(question):
    query = """
    MATCH (d:Document)-[:HAS_KEYWORD]->(k:Keyword)
    WHERE size(k.name) > 2 AND (toLower($question) CONTAINS toLower(k.name) OR toLower(k.name) CONTAINS toLower($question))
    RETURN d.file_name AS file,
           collect(k.name) AS keywords
    """
    with driver.session() as session:
        result = session.run(
            query,
            {"question": question}
        )
        return result.data()
