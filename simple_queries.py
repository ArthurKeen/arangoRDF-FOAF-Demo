#!/usr/bin/env python3
"""
Simple AQL Query Examples for ArangoRDF FOAF Demo

Working queries for the customer presentation.
"""

from arango import ArangoClient
import config

def main():
    print("="*60)
    print("ARANGORDF FOAF - SIMPLE QUERY EXAMPLES")
    print("="*60)
    
    # Connect to ArangoDB
    client = ArangoClient(hosts="http://localhost:8529")
    
    # Connect to databases
    rpt_db = client.db("FOAF-RPT", username="root", password="openSesame")
    pgt_db = client.db("FOAF-PGT", username="root", password="openSesame")
    
    print("\n1. RPT MODEL QUERIES")
    print("-" * 40)
    
    # RPT Query 1: Count total statements
    try:
        cursor = rpt_db.aql.execute("FOR stmt IN foaf_rpt_graph_Statement RETURN stmt LIMIT 5")
        results = list(cursor)
        print(f"Sample RDF statements (showing 5): {len(results)}")
        for i, stmt in enumerate(results):
            print(f"  {i+1}: {stmt['_from']} -> {stmt['_to']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # RPT Query 2: Count all statements
    try:
        cursor = rpt_db.aql.execute("RETURN LENGTH(foaf_rpt_graph_Statement)")
        total = list(cursor)[0]
        print(f"Total RDF statements: {total}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. PGT MODEL QUERIES")
    print("-" * 40)
    
    # PGT Query 1: Count persons
    try:
        cursor = pgt_db.aql.execute("RETURN LENGTH(Person)")
        total = list(cursor)[0]
        print(f"Total persons: {total}")
    except Exception as e:
        print(f"Error: {e}")
    
    # PGT Query 2: Find sample persons
    try:
        query = '''
        FOR person IN Person
        RETURN {
            name: person.`http://xmlns.com/foaf/0.1/name`,
            age: person.`http://xmlns.com/foaf/0.1/age`,
            title: person.`http://xmlns.com/foaf/0.1/title`
        }
        LIMIT 5
        '''
        cursor = pgt_db.aql.execute(query)
        results = list(cursor)
        print(f"Sample persons (showing 5):")
        for i, person in enumerate(results):
            print(f"  {i+1}: {person['name']} (age: {person['age']}, title: {person['title']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # PGT Query 3: Count relationships
    try:
        cursor = pgt_db.aql.execute("RETURN LENGTH(knows)")
        total = list(cursor)[0]
        print(f"Total 'knows' relationships: {total}")
    except Exception as e:
        print(f"Error: {e}")
    
    # PGT Query 4: Find people by age range
    try:
        query = '''
        FOR person IN Person
        FILTER person.`http://xmlns.com/foaf/0.1/age` >= 25 
        FILTER person.`http://xmlns.com/foaf/0.1/age` <= 35
        RETURN {
            name: person.`http://xmlns.com/foaf/0.1/name`,
            age: person.`http://xmlns.com/foaf/0.1/age`,
            title: person.`http://xmlns.com/foaf/0.1/title`
        }
        LIMIT 5
        '''
        cursor = pgt_db.aql.execute(query)
        results = list(cursor)
        print(f"People aged 25-35 (showing 5):")
        for i, person in enumerate(results):
            print(f"  {i+1}: {person['name']} (age: {person['age']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # PGT Query 5: Graph traversal
    try:
        query = '''
        FOR person IN Person
        LIMIT 1
        FOR friend IN 1..1 OUTBOUND person knows
        RETURN {
            person: person.`http://xmlns.com/foaf/0.1/name`,
            friend: friend.`http://xmlns.com/foaf/0.1/name`
        }
        LIMIT 3
        '''
        cursor = pgt_db.aql.execute(query)
        results = list(cursor)
        print(f"Friend connections (showing 3):")
        for i, conn in enumerate(results):
            print(f"  {i+1}: {conn['person']} knows {conn['friend']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n3. PERFORMANCE COMPARISON")
    print("-" * 40)
    
    # Compare model sizes
    for model_type, db_name in config.DATABASE_NAMES.items():
        try:
            db = client.db(db_name, username="root", password="openSesame")
            collections = db.collections()
            total_docs = 0
            for col in collections:
                if not col['name'].startswith('_'):
                    count = db.collection(col['name']).count()
                    total_docs += count
            print(f"{db_name}: {total_docs} total documents")
        except Exception as e:
            print(f"Error with {db_name}: {e}")
    
    print("\n" + "="*60)
    print("QUERY EXAMPLES COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main() 