#!/usr/bin/env python3
"""
Fix the FOAF-LPGT database to use proper LPGT transformation.
LPGT should have:
- One vertex collection called "Node"
- One edge collection called "relation"

Author: Arthur Keen
Date: January 2025
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Optional

from rdflib import Graph
from arango import ArangoClient
from arango_rdf import ArangoRDF
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LPGTDatabaseFixer:
    """Fix the LPGT database to use proper LPGT transformation"""
    
    def __init__(self):
        """Initialize the fixer with local Docker configuration"""
        self.db_config = config.LOCAL_CONFIG
        self.client = None
        self.sys_db = None
        self.lpgt_db = None
        self.arango_rdf = None
        
    def connect_to_arango(self) -> bool:
        """Connect to ArangoDB and set up system database"""
        try:
            logger.info(f"Connecting to ArangoDB at {self.db_config['host']}")
            self.client = ArangoClient(hosts=self.db_config["host"])
            
            self.sys_db = self.client.db(
                "_system",
                username=self.db_config["username"],
                password=self.db_config["password"]
            )
            
            # Test connection
            version_info = self.sys_db.version()
            logger.info(f"Successfully connected to ArangoDB {version_info}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            return False
    
    def load_foaf_data(self) -> Optional[Graph]:
        """Load FOAF RDF data from file"""
        try:
            logger.info("Loading FOAF RDF data...")
            foaf_graph = Graph()
            
            # Load the FOAF data file
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
        """Recreate the LPGT database with proper structure"""
        try:
            db_name = config.DATABASE_NAMES["lpgt"]  # FOAF-LPGT
            logger.info(f"Recreating database: {db_name}")
            
            # Drop existing database if it exists
            if self.sys_db.has_database(db_name):
                logger.info(f"Dropping existing database: {db_name}")
                self.sys_db.delete_database(db_name)
            
            # Create new database
            self.sys_db.create_database(db_name)
            
            # Connect to the new database
            self.lpgt_db = self.client.db(
                db_name,
                username=self.db_config["username"],
                password=self.db_config["password"]
            )
            
            self.arango_rdf = ArangoRDF(self.lpgt_db)
            logger.info(f"Database {db_name} recreated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recreate LPGT database: {e}")
            return False
    
    def load_lpgt_model(self, foaf_graph: Graph) -> bool:
        """Load data using LPGT (Labeled Property Graph Transformation)"""
        try:
            logger.info("Loading data using LPGT model...")
            logger.info("LPGT creates:")
            logger.info("- Single vertex collection: 'Node'")
            logger.info("- Edge collections for each relationship type")
            
            # Use PGT with resource_collection_name="Node" to create LPGT structure
            # This creates all vertices in a single "Node" collection
            self.arango_rdf.rdf_to_arangodb_by_pgt(
                name=config.GRAPH_NAMES["lpgt"],
                rdf_graph=foaf_graph,
                overwrite_graph=True,
                resource_collection_name="Node"  # Single vertex collection named "Node"
            )
            
            logger.info("LPGT model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load LPGT model: {e}")
            return False
    
    def verify_lpgt_structure(self) -> bool:
        """Verify the LPGT database has the correct structure"""
        try:
            logger.info("\nVerifying LPGT database structure...")
            
            collections = self.lpgt_db.collections()
            non_system_collections = [c for c in collections if not c['name'].startswith('_')]
            
            logger.info(f"Collections found: {[c['name'] for c in non_system_collections]}")
            
            # Check for Node collection (required)
            has_node = any(c['name'] == 'Node' for c in non_system_collections)
            
            if has_node:
                node_count = self.lpgt_db.collection('Node').count()
                
                # Get edge collections (should have at least one)
                edge_collections = [c for c in non_system_collections if c.get('type') == 3 or c['name'] != 'Node']
                
                logger.info(f"✅ LPGT structure verified:")
                logger.info(f"   - Node collection: {node_count} documents")
                logger.info(f"   - Edge collections ({len(edge_collections)}):")
                
                total_edges = 0
                for edge_col in edge_collections:
                    edge_count = self.lpgt_db.collection(edge_col['name']).count()
                    total_edges += edge_count
                    logger.info(f"     * {edge_col['name']}: {edge_count} documents")
                
                # Show sample documents
                if node_count > 0:
                    sample_node = list(self.lpgt_db.collection('Node').all(limit=1))[0]
                    logger.info(f"   Sample Node: {sample_node}")
                
                # Show sample edge if we have one named 'relation'
                if any(c['name'] == 'relation' for c in edge_collections):
                    relation_count = self.lpgt_db.collection('relation').count()
                    if relation_count > 0:
                        sample_relation = list(self.lpgt_db.collection('relation').all(limit=1))[0]
                        logger.info(f"   Sample relation: {sample_relation}")
                
                logger.info(f"   Total edges: {total_edges}")
                return True
            else:
                logger.error(f"❌ Missing required Node collection")
                logger.error(f"   Found collections: {[c['name'] for c in non_system_collections]}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying LPGT structure: {e}")
            return False
    
    def fix_lpgt_database(self) -> bool:
        """Run the complete LPGT database fix"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("FIXING FOAF-LPGT DATABASE")
        logger.info("="*60)
        
        # Step 1: Connect to ArangoDB
        if not self.connect_to_arango():
            return False
        
        # Step 2: Load FOAF RDF data
        foaf_graph = self.load_foaf_data()
        if foaf_graph is None:
            return False
        
        # Step 3: Recreate LPGT database
        if not self.recreate_lpgt_database():
            return False
        
        # Step 4: Load data using proper LPGT transformation
        if not self.load_lpgt_model(foaf_graph):
            return False
        
        # Step 5: Verify the structure
        if not self.verify_lpgt_structure():
            return False
        
        elapsed_time = time.time() - start_time
        logger.info(f"\nLPGT database fix completed successfully in {elapsed_time:.2f} seconds")
        
        return True


def main():
    """Main entry point"""
    logger.info("Fixing FOAF-LPGT database to use proper LPGT transformation...")
    logger.info("Target structure:")
    logger.info("- Single vertex collection: 'Node'")
    logger.info("- Single edge collection: 'relation'")
    
    fixer = LPGTDatabaseFixer()
    
    if fixer.fix_lpgt_database():
        logger.info("\n✅ FOAF-LPGT database fixed successfully!")
        logger.info("Database now has proper LPGT structure with Node and relation collections")
    else:
        logger.error("❌ Failed to fix LPGT database!")
        sys.exit(1)


if __name__ == "__main__":
    main()
