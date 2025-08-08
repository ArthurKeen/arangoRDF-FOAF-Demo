#!/usr/bin/env python3
"""
Manual creation of LPGT database with exact structure:
- Single vertex collection: 'Node'  
- Single edge collection: 'relation'

This approach manually transforms the RDF data to meet the LPGT requirements.

Author: Arthur Keen
Date: January 2025
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional, Set, Tuple
import json

from rdflib import Graph, URIRef, BNode, Literal
import config
from database_utils import LocalDatabaseManager
from logging_utils import setup_module_logging

# Set up logging
logger = setup_module_logging(__name__)


class LPGTManualCreator:
    """Manually create LPGT database with exact Node/relation structure"""
    
    def __init__(self):
        """Initialize the creator"""
        self.db_manager = LocalDatabaseManager()
        self.lpgt_db = None
        
    def connect_to_arango(self) -> bool:
        """Connect to ArangoDB"""
        try:
            self.db_manager.connect_to_system_db()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            return False
    
    def load_foaf_data(self) -> Optional[Graph]:
        """Load FOAF RDF data"""
        try:
            logger.info("Loading FOAF RDF data...")
            foaf_graph = Graph()
            
            data_path = config.DATA_PATHS["foaf_data"]
            if not Path(data_path).exists():
                logger.error(f"FOAF data file not found: {data_path}")
                return None
                
            foaf_graph.parse(data_path, format="turtle")
            logger.info(f"Loaded {len(foaf_graph)} RDF triples")
            
            return foaf_graph
            
        except Exception as e:
            logger.error(f"Failed to load FOAF data: {e}")
            return None
    
    def recreate_lpgt_database(self) -> bool:
        """Recreate the LPGT database"""
        try:
            db_name = config.DATABASE_NAMES["lpgt"]  # FOAF-LPGT
            logger.info(f"Recreating database: {db_name}")
            
            # Use database manager to recreate database
            self.lpgt_db = self.db_manager.recreate_database(db_name)
            
            logger.info(f"Database {db_name} recreated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recreate LPGT database: {e}")
            return False
    
    def create_collections(self) -> bool:
        """Create Node vertex collection and relation edge collection"""
        try:
            logger.info("Creating LPGT collections...")
            
            # Create Node vertex collection
            if not self.lpgt_db.has_collection('Node'):
                self.lpgt_db.create_collection('Node')
                logger.info("Created 'Node' vertex collection")
            
            # Create relation edge collection
            if not self.lpgt_db.has_collection('relation'):
                self.lpgt_db.create_collection('relation', edge=True)
                logger.info("Created 'relation' edge collection")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collections: {e}")
            return False
    
    def transform_rdf_to_lpgt(self, foaf_graph: Graph) -> bool:
        """Manually transform RDF data to LPGT structure"""
        try:
            logger.info("Transforming RDF data to LPGT structure...")
            
            node_collection = self.lpgt_db.collection('Node')
            relation_collection = self.lpgt_db.collection('relation')
            
            # Step 1: Extract all unique subjects and objects as nodes
            nodes = set()
            node_data = {}
            
            logger.info("Extracting nodes and properties...")
            for subject, predicate, obj in foaf_graph:
                # Add subject as node
                if isinstance(subject, (URIRef, BNode)):
                    nodes.add(subject)
                
                # Add object as node if it's a URI or BNode
                if isinstance(obj, (URIRef, BNode)):
                    nodes.add(obj)
                
                # Collect properties for each subject
                if isinstance(subject, (URIRef, BNode)):
                    if subject not in node_data:
                        node_data[subject] = {
                            '_uri': str(subject) if isinstance(subject, URIRef) else None,
                            '_label': str(subject).split('/')[-1] if isinstance(subject, URIRef) else str(subject),
                            '_rdftype': 'URIRef' if isinstance(subject, URIRef) else 'BNode'
                        }
                    
                    # Add literal properties directly to the node using localname
                    if isinstance(obj, Literal):
                        # Extract localname from predicate IRI
                        pred_str = str(predicate)
                        if '#' in pred_str:
                            prop_key = pred_str.split('#')[-1]
                        elif '/' in pred_str:
                            prop_key = pred_str.split('/')[-1]
                        else:
                            prop_key = pred_str
                        
                        # Handle datatype conversion
                        if obj.datatype:
                            if 'integer' in str(obj.datatype) or 'int' in str(obj.datatype):
                                try:
                                    node_data[subject][prop_key] = int(obj)
                                except:
                                    node_data[subject][prop_key] = str(obj)
                            elif 'float' in str(obj.datatype) or 'double' in str(obj.datatype):
                                try:
                                    node_data[subject][prop_key] = float(obj)
                                except:
                                    node_data[subject][prop_key] = str(obj)
                            else:
                                node_data[subject][prop_key] = str(obj)
                        else:
                            node_data[subject][prop_key] = str(obj)
            
            # Step 2: Insert nodes into Node collection
            logger.info(f"Inserting {len(nodes)} nodes...")
            node_key_map = {}  # Map RDF node to ArangoDB _key
            
            for node in nodes:
                node_doc = node_data.get(node, {
                    '_uri': str(node) if isinstance(node, URIRef) else None,
                    '_label': str(node).split('/')[-1] if isinstance(node, URIRef) else str(node),
                    '_rdftype': 'URIRef' if isinstance(node, URIRef) else 'BNode'
                })
                
                # Insert node and get the _key
                result = node_collection.insert(node_doc)
                node_key_map[node] = result['_key']
            
            logger.info(f"Inserted {len(node_key_map)} nodes into Node collection")
            
            # Step 3: Create relations for non-literal triples
            logger.info("Creating relations...")
            relations = []
            
            for subject, predicate, obj in foaf_graph:
                # Only create relations for non-literal objects
                if isinstance(obj, (URIRef, BNode)) and subject in node_key_map and obj in node_key_map:
                    # Extract localname from predicate IRI for label
                    pred_str = str(predicate)
                    if '#' in pred_str:
                        pred_localname = pred_str.split('#')[-1]
                    elif '/' in pred_str:
                        pred_localname = pred_str.split('/')[-1]
                    else:
                        pred_localname = pred_str
                    
                    relation_doc = {
                        '_from': f"Node/{node_key_map[subject]}",
                        '_to': f"Node/{node_key_map[obj]}",
                        'predicate': str(predicate),
                        'predicate_label': pred_localname,
                        '_rdftype': 'ObjectProperty'
                    }
                    relations.append(relation_doc)
            
            # Batch insert relations
            if relations:
                relation_collection.insert_many(relations)
                logger.info(f"Inserted {len(relations)} relations into relation collection")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to transform RDF to LPGT: {e}")
            return False
    
    def create_graph_definition(self) -> bool:
        """Create graph definition for traversals"""
        try:
            graph_name = config.GRAPH_NAMES["lpgt"]
            
            if self.lpgt_db.has_graph(graph_name):
                self.lpgt_db.delete_graph(graph_name)
            
            graph = self.lpgt_db.create_graph(graph_name)
            graph.create_vertex_collection('Node')
            graph.create_edge_definition(
                edge_collection='relation',
                from_vertex_collections=['Node'],
                to_vertex_collections=['Node']
            )
            
            logger.info(f"Created graph definition: {graph_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create graph definition: {e}")
            return False
    
    def verify_lpgt_structure(self) -> bool:
        """Verify the correct LPGT structure"""
        try:
            logger.info("\n" + "="*50)
            logger.info("VERIFYING LPGT STRUCTURE")
            logger.info("="*50)
            
            collections = self.lpgt_db.collections()
            non_system_collections = [c for c in collections if not c['name'].startswith('_')]
            
            logger.info(f"Collections: {[c['name'] for c in non_system_collections]}")
            
            # Check for exactly Node and relation collections
            collection_names = [c['name'] for c in non_system_collections]
            
            if 'Node' in collection_names and 'relation' in collection_names and len(collection_names) == 2:
                node_count = self.lpgt_db.collection('Node').count()
                relation_count = self.lpgt_db.collection('relation').count()
                
                logger.info(f"✅ Perfect LPGT structure:")
                logger.info(f"   - Node collection: {node_count} documents")
                logger.info(f"   - relation collection: {relation_count} documents")
                
                # Show samples
                if node_count > 0:
                    sample_node = list(self.lpgt_db.collection('Node').all(limit=1))[0]
                    logger.info(f"   Sample Node (with localname properties): {json.dumps(sample_node, indent=4)[:300]}...")
                
                if relation_count > 0:
                    sample_relation = list(self.lpgt_db.collection('relation').all(limit=1))[0]
                    logger.info(f"   Sample relation: {sample_relation}")
                
                # Show a Person node specifically to demonstrate localnames
                person_cursor = self.lpgt_db.aql.execute("""
                    FOR node IN Node
                    FILTER node._rdftype == "URIRef" AND node.name != null
                    LIMIT 1
                    RETURN node
                """)
                person_nodes = list(person_cursor)
                if person_nodes:
                    logger.info(f"   Sample Person with localnames: {person_nodes[0]}")
                
                return True
            else:
                logger.error(f"❌ Incorrect structure. Expected only 'Node' and 'relation' collections")
                logger.error(f"   Found: {collection_names}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying structure: {e}")
            return False
    
    def create_lpgt_database(self) -> bool:
        """Run the complete LPGT database creation"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("CREATING PROPER LPGT DATABASE")
        logger.info("Target structure:")
        logger.info("- Single vertex collection: 'Node'")
        logger.info("- Single edge collection: 'relation'")
        logger.info("="*60)
        
        # Step 1: Connect
        if not self.connect_to_arango():
            return False
        
        # Step 2: Load RDF data
        foaf_graph = self.load_foaf_data()
        if foaf_graph is None:
            return False
        
        # Step 3: Recreate database
        if not self.recreate_lpgt_database():
            return False
        
        # Step 4: Create collections
        if not self.create_collections():
            return False
        
        # Step 5: Transform and load data
        if not self.transform_rdf_to_lpgt(foaf_graph):
            return False
        
        # Step 6: Create graph definition
        if not self.create_graph_definition():
            return False
        
        # Step 7: Verify structure
        if not self.verify_lpgt_structure():
            return False
        
        elapsed_time = time.time() - start_time
        logger.info(f"\n✅ LPGT database created successfully in {elapsed_time:.2f} seconds")
        
        return True


def main():
    """Main entry point"""
    creator = LPGTManualCreator()
    
    if creator.create_lpgt_database():
        logger.info("\n🎉 FOAF-LPGT database created with correct structure!")
    else:
        logger.error("❌ Failed to create LPGT database!")
        sys.exit(1)


if __name__ == "__main__":
    main()
