#!/usr/bin/env python3
"""
AQL Query Demonstration for ArangoRDF FOAF Data

This script demonstrates various AQL queries across the three different
FOAF database models:
1. RPT (RDF-Topology Preserving Transformation)
2. PGT (Property Graph Transformation)
3. PGT-Node (Property Graph with single vertex collection)

Author: Arthur Keen
Date: January 2025
"""

import logging
import json
from typing import Dict, List, Any

from arango import ArangoClient
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FOAFQueryDemo:
    """Demonstration class for AQL queries on FOAF data"""
    
    def __init__(self, use_cloud: bool = False):
        """Initialize the query demo with local or cloud configuration"""
        self.use_cloud = use_cloud
        self.db_config = config.CLOUD_CONFIG if use_cloud else config.LOCAL_CONFIG
        self.client = None
        self.databases = {}
        
    def connect_to_databases(self) -> bool:
        """Connect to all three FOAF databases"""
        try:
            logger.info(f"Connecting to ArangoDB at {self.db_config['host']}")
            self.client = ArangoClient(hosts=self.db_config["host"])
            
            for model_type, db_name in config.DATABASE_NAMES.items():
                db = self.client.db(
                    db_name,
                    username=self.db_config["username"],
                    password=self.db_config["password"]
                )
                self.databases[model_type] = db
                
            logger.info("Connected to all databases successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            return False
    
    def execute_query(self, db_name: str, query: str, description: str) -> List[Dict[str, Any]]:
        """Execute an AQL query and return results"""
        try:
            logger.info(f"\n{description}")
            logger.info(f"Database: {db_name}")
            logger.info(f"Query: {query}")
            logger.info("-" * 60)
            
            cursor = self.databases[db_name].aql.execute(query)
            results = list(cursor)
            
            logger.info(f"Results ({len(results)} rows):")
            for i, result in enumerate(results[:5]):  # Show first 5 results
                logger.info(f"  {i+1}: {json.dumps(result, indent=2, default=str)}")
            
            if len(results) > 5:
                logger.info(f"  ... and {len(results) - 5} more rows")
                
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def demo_rpt_queries(self):
        """Demonstrate queries on RPT database"""
        logger.info("\n" + "="*60)
        logger.info("RPT (RDF-TOPOLOGY PRESERVING) QUERIES")
        logger.info("="*60)
        
        # Query 1: Count all triples
        self.execute_query(
            "rpt",
            f"FOR triple IN {config.GRAPH_NAMES['rpt']}_edge RETURN {{subject: triple._from, predicate: triple.`rdf-type`, object: triple._to}}",
            "Count all RDF triples (edges)"
        )
        
        # Query 2: Find all people (subjects with type foaf:Person)
        self.execute_query(
            "rpt", 
            f"""
            FOR edge IN {config.GRAPH_NAMES['rpt']}_edge
            FILTER edge.`rdf-type` == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
            FILTER edge._to LIKE "%foaf/0.1/Person"
            RETURN DISTINCT edge._from
            """,
            "Find all FOAF Person entities"
        )
        
        # Query 3: Find people and their names
        self.execute_query(
            "rpt",
            f"""
            FOR person_edge IN {config.GRAPH_NAMES['rpt']}_edge
            FILTER person_edge.`rdf-type` == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
            FILTER person_edge._to LIKE "%foaf/0.1/Person"
            
            FOR name_edge IN {config.GRAPH_NAMES['rpt']}_edge
            FILTER name_edge._from == person_edge._from
            FILTER name_edge.`rdf-type` LIKE "%foaf/0.1/name"
            
            RETURN {{
                person: person_edge._from,
                name: name_edge._to
            }}
            """,
            "Find people and their names"
        )
        
        # Query 4: Find friendship connections
        self.execute_query(
            "rpt",
            f"""
            FOR knows_edge IN {config.GRAPH_NAMES['rpt']}_edge
            FILTER knows_edge.`rdf-type` LIKE "%foaf/0.1/knows"
            RETURN {{
                person1: knows_edge._from,
                person2: knows_edge._to,
                relationship: "knows"
            }}
            LIMIT 10
            """,
            "Find friendship connections (knows relationships)"
        )
    
    def demo_pgt_queries(self):
        """Demonstrate queries on PGT database"""
        logger.info("\n" + "="*60)
        logger.info("PGT (PROPERTY GRAPH TRANSFORMATION) QUERIES")
        logger.info("="*60)
        
        # Query 1: Find all Person documents with their properties
        self.execute_query(
            "pgt",
            """
            FOR person IN Person
            RETURN {
                key: person._key,
                name: person.`http://xmlns.com/foaf/0.1/name`,
                firstName: person.`http://xmlns.com/foaf/0.1/firstName`,
                familyName: person.`http://xmlns.com/foaf/0.1/familyName`,
                age: person.`http://xmlns.com/foaf/0.1/age`,
                email: person.`http://xmlns.com/foaf/0.1/mbox`,
                title: person.`http://xmlns.com/foaf/0.1/title`
            }
            LIMIT 10
            """,
            "Find Person documents with their properties"
        )
        
        # Query 2: Find people by age range
        self.execute_query(
            "pgt",
            """
            FOR person IN Person
            FILTER person.`http://xmlns.com/foaf/0.1/age` != null
            FILTER person.`http://xmlns.com/foaf/0.1/age` >= 25 AND person.`http://xmlns.com/foaf/0.1/age` <= 35
            RETURN {
                name: person.`http://xmlns.com/foaf/0.1/name`,
                age: person.`http://xmlns.com/foaf/0.1/age`,
                title: person.`http://xmlns.com/foaf/0.1/title`
            }
            SORT person.`http://xmlns.com/foaf/0.1/age`
            """,
            "Find people aged 25-35"
        )
        
        # Query 3: Find social network connections with person details
        self.execute_query(
            "pgt",
            """
            FOR edge IN knows
            FOR person1 IN Person
            FILTER person1._id == edge._from
            FOR person2 IN Person  
            FILTER person2._id == edge._to
            RETURN {
                person1_name: person1.`http://xmlns.com/foaf/0.1/name`,
                person1_title: person1.`http://xmlns.com/foaf/0.1/title`,
                person2_name: person2.`http://xmlns.com/foaf/0.1/name`,
                person2_title: person2.`http://xmlns.com/foaf/0.1/title`,
                relationship: "knows"
            }
            LIMIT 10
            """,
            "Social network connections with person details"
        )
        
        # Query 4: Find people with specific interests
        self.execute_query(
            "pgt",
            """
            FOR person IN Person
            FILTER person.`http://xmlns.com/foaf/0.1/interest` != null
            RETURN {
                name: person.`http://xmlns.com/foaf/0.1/name`,
                interests: person.`http://xmlns.com/foaf/0.1/interest`,
                title: person.`http://xmlns.com/foaf/0.1/title`
            }
            LIMIT 10
            """,
            "Find people with their interests"
        )
        
        # Query 5: Graph traversal - find friends of friends
        self.execute_query(
            "pgt",
            """
            FOR person IN Person
            FILTER person.`http://xmlns.com/foaf/0.1/name` != null
            LIMIT 1
            
            FOR v, e, p IN 2..2 OUTBOUND person._id knows
            RETURN {
                start_person: person.`http://xmlns.com/foaf/0.1/name`,
                friend_of_friend: v.`http://xmlns.com/foaf/0.1/name`,
                path_length: LENGTH(p.edges)
            }
            LIMIT 10
            """,
            "Find friends of friends (2-hop traversal)"
        )
    
    def demo_pgt_node_queries(self):
        """Demonstrate queries on PGT-Node database"""
        logger.info("\n" + "="*60) 
        logger.info("PGT-NODE (SINGLE NODE COLLECTION) QUERIES")
        logger.info("="*60)
        
        # Query 1: Count entities by type
        self.execute_query(
            "pgt_node",
            """
            LET types = (
                FOR t IN type
                FOR c IN Class
                FILTER t._to == c._id
                COLLECT class = c._uri WITH COUNT INTO count
                RETURN { type: class, count: count }
            )
            FOR t IN types
            SORT t.count DESC
            RETURN t
            """,
            "Count entities by type in Node collection"
        )
        
        # Query 2: Find Person entities with their properties
        self.execute_query(
            "pgt_node",
            """
            LET person_class = FIRST(
                FOR c IN Class
                FILTER c._uri == 'http://xmlns.com/foaf/0.1/Person'
                RETURN c._id
            )
            LET persons = (
                FOR t IN type
                FILTER t._to == person_class
                FOR node IN Node
                FILTER node._id == t._from
                LIMIT 10
                RETURN {
                    key: node._key,
                    name: node.name,
                    firstName: node.firstName,
                    familyName: node.familyName,
                    age: node.age,
                    title: node.title
                }
            )
            RETURN persons
            """,
            "Find Person entities with their properties"
        )
        
        # Query 3: Find people by age range
        self.execute_query(
            "pgt_node",
            """
            LET person_class = FIRST(
                FOR c IN Class
                FILTER c._uri == 'http://xmlns.com/foaf/0.1/Person'
                RETURN c._id
            )
            LET persons = (
                FOR t IN type
                FILTER t._to == person_class
                FOR node IN Node
                FILTER node._id == t._from
                FILTER node.age != null
                FILTER node.age >= 25 AND node.age <= 35
                SORT node.age
                RETURN {
                    name: node.name,
                    age: node.age,
                    title: node.title
                }
            )
            RETURN persons
            """,
            "Find people aged 25-35"
        )
        
        # Query 4: Analyze network connections
        self.execute_query(
            "pgt_node",
            """
            LET person_class = FIRST(
                FOR c IN Class
                FILTER c._uri == 'http://xmlns.com/foaf/0.1/Person'
                RETURN c._id
            )
            LET persons = (
                FOR t IN type
                FILTER t._to == person_class
                FOR node IN Node
                FILTER node._id == t._from
                
                LET outgoing_knows = (
                    FOR edge IN knows
                    FILTER edge._from == node._id
                    RETURN 1
                )
                
                LET incoming_knows = (
                    FOR edge IN knows
                    FILTER edge._to == node._id
                    RETURN 1
                )
                
                LET total_connections = LENGTH(outgoing_knows) + LENGTH(incoming_knows)
                
                FILTER total_connections > 0
                SORT total_connections DESC
                LIMIT 10
                
                RETURN {
                    name: node.name,
                    title: node.title,
                    outgoing_count: LENGTH(outgoing_knows),
                    incoming_count: LENGTH(incoming_knows),
                    total_connections: total_connections
                }
            )
            RETURN persons
            """,
            "Find most connected people in the network"
        )
    
    def demo_comparative_queries(self):
        """Demonstrate comparative queries across all models"""
        logger.info("\n" + "="*60)
        logger.info("COMPARATIVE QUERIES ACROSS ALL MODELS")
        logger.info("="*60)
        
        # Count total entities in each model
        for model_type, db_name in config.DATABASE_NAMES.items():
            try:
                if model_type == "rpt":
                    # For RPT, count vertices
                    result = self.execute_query(
                        model_type,
                        f"FOR vertex IN {config.GRAPH_NAMES['rpt']}_vertex RETURN vertex",
                        f"Total vertices in {db_name}"
                    )
                elif model_type == "pgt":
                    # For PGT, count Person documents
                    result = self.execute_query(
                        model_type,
                        "FOR person IN Person RETURN person",
                        f"Total Person documents in {db_name}"
                    )
                else:  # pgt_node
                    # For PGT-Node, count Person nodes
                    result = self.execute_query(
                        model_type,
                        """
                        LET person_class = FIRST(
                            FOR c IN Class
                            FILTER c._uri == 'http://xmlns.com/foaf/0.1/Person'
                            RETURN c._id
                        )
                        FOR t IN type
                        FILTER t._to == person_class
                        FOR node IN Node
                        FILTER node._id == t._from
                        RETURN node
                        """,
                        f"Total Person nodes in {db_name}"
                    )
                    
                logger.info(f"Total count: {len(result)}")
                
            except Exception as e:
                logger.error(f"Error counting entities in {db_name}: {e}")
    
    def run_demo(self) -> bool:
        """Run the complete query demonstration"""
        logger.info("="*60)
        logger.info("ARANGORDF FOAF QUERY DEMONSTRATION")
        logger.info("="*60)
        
        # Connect to databases
        if not self.connect_to_databases():
            return False
        
        # Run queries for each model
        self.demo_rpt_queries()
        self.demo_pgt_queries()
        self.demo_pgt_node_queries()
        self.demo_comparative_queries()
        
        logger.info("\n" + "="*60)
        logger.info("QUERY DEMONSTRATION COMPLETED")
        logger.info("="*60)
        
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArangoRDF FOAF Query Demonstration")
    parser.add_argument(
        "--cloud", 
        action="store_true", 
        help="Use cloud ArangoDB instance instead of local"
    )
    
    args = parser.parse_args()
    
    if args.cloud and not config.CLOUD_CONFIG["password"]:
        logger.error("Cloud password not set. Please set ARANGO_CLOUD_PASSWORD environment variable.")
        return False
    
    demo = FOAFQueryDemo(use_cloud=args.cloud)
    
    if demo.run_demo():
        logger.info("Query demonstration completed successfully!")
        return True
    else:
        logger.error("Query demonstration failed!")
        return False


if __name__ == "__main__":
    main() 