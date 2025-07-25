#!/usr/bin/env python3
"""
Customer Demo Script - ArangoRDF FOAF Demonstration
Perfect for Monday customer presentation!
"""

from arango import ArangoClient

def main():
    print("🎉 ARANGORDF FOAF CUSTOMER DEMONSTRATION")
    print("="*60)
    
    # Connect to databases
    client = ArangoClient(hosts="http://localhost:8529")
    pgt_db = client.db("FOAF-PGT", username="root", password="openSesame")
    rpt_db = client.db("FOAF-RPT", username="root", password="openSesame")
    
    print("\n📊 DATABASE OVERVIEW:")
    pgt_persons = list(pgt_db.aql.execute("RETURN LENGTH(Person)"))[0]
    rpt_triples = list(rpt_db.aql.execute("RETURN LENGTH(foaf_rpt_graph_Statement)"))[0]
    relationships = list(pgt_db.aql.execute("RETURN LENGTH(knows)"))[0]
    
    print(f"  • FOAF Persons: {pgt_persons:,}")
    print(f"  • RDF Triples: {rpt_triples:,}")
    print(f"  • Social Connections: {relationships:,}")
    
    print("\n🎯 DEMO QUERY 1 - Person Details:")
    print("AQL: FOR person IN Person RETURN person")
    results = list(pgt_db.aql.execute("FOR person IN Person RETURN person"))
    print(f"✅ Found {len(results)} people")
    for i, person in enumerate(results[:3]):
        name = person.get('name', 'Unknown')
        age = person.get('age', 'Unknown')
        title = person.get('title', 'Unknown')
        print(f"  • {name} (age: {age}, {title})")
    
    print("\n🎯 DEMO QUERY 2 - Age Filtering:")
    print("AQL: FOR person IN Person FILTER person.age >= 40 RETURN person")
    results = list(pgt_db.aql.execute("FOR person IN Person FILTER person.age >= 40 RETURN person"))
    print(f"✅ Found {len(results)} people aged 40+")
    for i, person in enumerate(results[:3]):
        name = person.get('name', 'Unknown')
        age = person.get('age', 'Unknown')
        print(f"  • {name} (age: {age})")
    
    print("\n🎯 DEMO QUERY 3 - Job Title Search:")
    print("AQL: FOR person IN Person FILTER person.title LIKE '%Manager%' RETURN person")
    results = list(pgt_db.aql.execute("FOR person IN Person FILTER person.title LIKE '%Manager%' RETURN person"))
    print(f"✅ Found {len(results)} managers")
    for i, person in enumerate(results[:3]):
        name = person.get('name', 'Unknown')
        title = person.get('title', 'Unknown')
        print(f"  • {name} - {title}")
    
    print("\n🎯 DEMO QUERY 4 - Social Network Analysis:")
    print("AQL: FOR person IN Person FOR friend IN 1..1 OUTBOUND person knows RETURN {person, friend}")
    results = list(pgt_db.aql.execute("FOR person IN Person FOR friend IN 1..1 OUTBOUND person knows RETURN {person: person.name, friend: friend.name}"))
    print(f"✅ Found {len(results)} friendship connections")
    for i, conn in enumerate(results[:3]):
        person_name = conn.get('person', 'Unknown')
        friend_name = conn.get('friend', 'Unknown')
        print(f"  • {person_name} knows {friend_name}")
    
    print("\n⚡ KEY ADVANTAGES:")
    print("  ✅ Native AQL queries (no SPARQL translation)")
    print("  ✅ Multiple data models from same source")
    print("  ✅ High-performance graph traversals")
    print("  ✅ Real-world scale: 300 people, 10K+ triples")
    
    print("\n🌐 GitHub: https://github.com/ArthurKeen/arangoRDF-FOAF-Demo")
    print("🎉 Demo Complete - Ready for Customer Presentation!")

if __name__ == "__main__":
    main() 