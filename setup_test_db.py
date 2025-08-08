#!/usr/bin/env python3
"""
Setup script to prepare the EntityResolutionExample database for FOAF demo testing.
This script will:
1. Connect to the existing database
2. Examine current Person collection
3. Add additional Person documents with FOAF properties
4. Create 'knows' edge collection and relationships
"""

from arango import ArangoClient
import json

# Database configuration
DB_CONFIG = {
    "host": "http://localhost:8529",
    "username": "root", 
    "password": "openSesame",
    "database": "EntityResolutionExample"
}

def connect_to_database():
    """Connect to the ArangoDB database"""
    client = ArangoClient(hosts=DB_CONFIG["host"])
    db = client.db(
        name=DB_CONFIG["database"],
        username=DB_CONFIG["username"],
        password=DB_CONFIG["password"]
    )
    return db

def examine_current_structure(db):
    """Examine the current database structure"""
    print("=== Current Database Structure ===")
    
    # List all collections
    collections = db.collections()
    print(f"Collections: {[c['name'] for c in collections if not c['name'].startswith('_')]}")
    
    # Examine Person collection
    if db.has_collection('Person'):
        person_collection = db.collection('Person')
        person_count = person_collection.count()
        print(f"Person collection count: {person_count}")
        
        # Get a sample person to see the structure
        if person_count > 0:
            sample_person = list(person_collection.all(limit=1))[0]
            print(f"Sample Person document:")
            print(json.dumps(sample_person, indent=2))
    
    return True

def add_foaf_persons(db):
    """Add Person documents with FOAF-compatible properties"""
    person_collection = db.collection('Person')
    
    # Additional persons with FOAF properties
    foaf_persons = [
        {
            "http://xmlns.com/foaf/0.1/name": "Alice Johnson",
            "http://xmlns.com/foaf/0.1/age": 28,
            "http://xmlns.com/foaf/0.1/title": "Software Engineer",
            "http://xmlns.com/foaf/0.1/email": "alice.johnson@example.com",
            "http://xmlns.com/foaf/0.1/interest": ["programming", "hiking", "photography"],
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://xmlns.com/foaf/0.1/Person"
        },
        {
            "http://xmlns.com/foaf/0.1/name": "Bob Smith",
            "http://xmlns.com/foaf/0.1/age": 35,
            "http://xmlns.com/foaf/0.1/title": "Data Scientist",
            "http://xmlns.com/foaf/0.1/email": "bob.smith@example.com",
            "http://xmlns.com/foaf/0.1/interest": ["machine learning", "cycling", "cooking"],
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://xmlns.com/foaf/0.1/Person"
        },
        {
            "http://xmlns.com/foaf/0.1/name": "Carol Williams",
            "http://xmlns.com/foaf/0.1/age": 31,
            "http://xmlns.com/foaf/0.1/title": "Product Manager",
            "http://xmlns.com/foaf/0.1/email": "carol.williams@example.com",
            "http://xmlns.com/foaf/0.1/interest": ["design", "travel", "reading"],
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://xmlns.com/foaf/0.1/Person"
        },
        {
            "http://xmlns.com/foaf/0.1/name": "David Brown",
            "http://xmlns.com/foaf/0.1/age": 42,
            "http://xmlns.com/foaf/0.1/title": "Engineering Manager",
            "http://xmlns.com/foaf/0.1/email": "david.brown@example.com",
            "http://xmlns.com/foaf/0.1/interest": ["leadership", "golf", "music"],
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://xmlns.com/foaf/0.1/Person"
        },
        {
            "http://xmlns.com/foaf/0.1/name": "Eva Garcia",
            "http://xmlns.com/foaf/0.1/age": 26,
            "http://xmlns.com/foaf/0.1/title": "UX Designer",
            "http://xmlns.com/foaf/0.1/email": "eva.garcia@example.com",
            "http://xmlns.com/foaf/0.1/interest": ["design", "art", "yoga"],
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://xmlns.com/foaf/0.1/Person"
        },
        {
            "http://xmlns.com/foaf/0.1/name": "Frank Miller",
            "http://xmlns.com/foaf/0.1/age": 39,
            "http://xmlns.com/foaf/0.1/title": "DevOps Engineer",
            "http://xmlns.com/foaf/0.1/email": "frank.miller@example.com",
            "http://xmlns.com/foaf/0.1/interest": ["automation", "climbing", "gaming"],
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://xmlns.com/foaf/0.1/Person"
        }
    ]
    
    inserted_persons = []
    for person in foaf_persons:
        result = person_collection.insert(person)
        inserted_persons.append(result)
        print(f"Added person: {person['http://xmlns.com/foaf/0.1/name']} -> {result['_id']}")
    
    return inserted_persons

def create_knows_collection(db):
    """Create the 'knows' edge collection"""
    if not db.has_collection('knows'):
        knows_collection = db.create_collection('knows', edge=True)
        print("Created 'knows' edge collection")
    else:
        knows_collection = db.collection('knows')
        print("'knows' collection already exists")
    
    return knows_collection

def create_knows_relationships(db, persons):
    """Create 'knows' relationships between persons"""
    knows_collection = db.collection('knows')
    person_collection = db.collection('Person')
    
    # Get all persons (existing + newly added)
    all_persons = list(person_collection.all())
    person_ids = [p['_id'] for p in all_persons]
    
    print(f"Found {len(person_ids)} total persons in database")
    
    # Create some friendship relationships
    relationships = [
        # Alice knows Bob and Carol
        (0, 1), (0, 2),
        # Bob knows Alice, Carol, and David
        (1, 0), (1, 2), (1, 3),
        # Carol knows Alice, Bob, and Eva
        (2, 0), (2, 1), (2, 4),
        # David knows Bob and Frank
        (3, 1), (3, 5),
        # Eva knows Carol and Frank
        (4, 2), (4, 5),
        # Frank knows David and Eva
        (5, 3), (5, 4)
    ]
    
    created_edges = []
    for from_idx, to_idx in relationships:
        if from_idx < len(person_ids) and to_idx < len(person_ids):
            edge = {
                "_from": person_ids[from_idx],
                "_to": person_ids[to_idx],
                "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://xmlns.com/foaf/0.1/knows"
            }
            result = knows_collection.insert(edge)
            created_edges.append(result)
            
            # Get person names for logging
            from_person = person_collection.get(person_ids[from_idx])
            to_person = person_collection.get(person_ids[to_idx])
            from_name = from_person.get('http://xmlns.com/foaf/0.1/name', 'Unknown')
            to_name = to_person.get('http://xmlns.com/foaf/0.1/name', 'Unknown')
            
            print(f"Created relationship: {from_name} knows {to_name}")
    
    return created_edges

def create_graph_if_needed(db):
    """Create a graph definition for traversals"""
    graph_name = "foaf_test_graph"
    
    if not db.has_graph(graph_name):
        graph = db.create_graph(graph_name)
        # Add vertex collection
        graph.create_vertex_collection('Person')
        # Add edge definition
        graph.create_edge_definition(
            edge_collection='knows',
            from_vertex_collections=['Person'],
            to_vertex_collections=['Person']
        )
        print(f"Created graph: {graph_name}")
    else:
        print(f"Graph {graph_name} already exists")

def test_foaf_queries(db):
    """Test some FOAF-style queries on the setup database"""
    print("\n=== Testing FOAF Queries ===")
    
    # Query 1: Find all persons with their names and ages
    print("\n1. All persons with names and ages:")
    cursor = db.aql.execute("""
        FOR person IN Person
        FILTER person.`http://xmlns.com/foaf/0.1/name` != null
        RETURN {
            name: person.`http://xmlns.com/foaf/0.1/name`,
            age: person.`http://xmlns.com/foaf/0.1/age`,
            title: person.`http://xmlns.com/foaf/0.1/title`
        }
    """)
    for result in cursor:
        print(f"  - {result}")
    
    # Query 2: Find friendship connections
    print("\n2. Friendship connections:")
    cursor = db.aql.execute("""
        FOR edge IN knows
        LET from_person = DOCUMENT(edge._from)
        LET to_person = DOCUMENT(edge._to)
        RETURN {
            from: from_person.`http://xmlns.com/foaf/0.1/name`,
            to: to_person.`http://xmlns.com/foaf/0.1/name`
        }
    """)
    for result in cursor:
        print(f"  - {result['from']} knows {result['to']}")
    
    # Query 3: Find persons by age range
    print("\n3. Persons aged 25-35:")
    cursor = db.aql.execute("""
        FOR person IN Person
        FILTER person.`http://xmlns.com/foaf/0.1/age` >= 25 
           AND person.`http://xmlns.com/foaf/0.1/age` <= 35
        RETURN {
            name: person.`http://xmlns.com/foaf/0.1/name`,
            age: person.`http://xmlns.com/foaf/0.1/age`,
            title: person.`http://xmlns.com/foaf/0.1/title`
        }
    """)
    for result in cursor:
        print(f"  - {result}")

def main():
    """Main setup function"""
    print("Setting up EntityResolutionExample database for FOAF demo testing...")
    
    try:
        # Connect to database
        db = connect_to_database()
        print(f"Connected to database: {DB_CONFIG['database']}")
        
        # Examine current structure
        examine_current_structure(db)
        
        # Add FOAF persons
        print("\n=== Adding FOAF-compatible Person documents ===")
        persons = add_foaf_persons(db)
        
        # Create knows collection
        print("\n=== Setting up 'knows' relationships ===")
        create_knows_collection(db)
        
        # Create relationships
        create_knows_relationships(db, persons)
        
        # Create graph definition
        print("\n=== Creating graph definition ===")
        create_graph_if_needed(db)
        
        # Test queries
        test_foaf_queries(db)
        
        print("\n✅ Database setup complete! Ready for FOAF demo testing.")
        print(f"Database: {DB_CONFIG['database']}")
        print("Collections: Person, Company, Address, Phone, hasPhone, hasAddress, knows")
        print("Graph: foaf_test_graph")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        raise

if __name__ == "__main__":
    main()
