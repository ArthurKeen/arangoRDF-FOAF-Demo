#!/usr/bin/env python3
"""
Fix PGT FOAF Databases Script

This script drops and recreates the PGT FOAF databases with contextualize_graph=True
to properly handle ontology imports and eliminate UnknownResource collections.

Author: Arthur Keen
Date: January 2025
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Optional
import os

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


class FOAFPGTFixer:
    """Fix PGT databases with proper ontology contextualization"""
    
    def __init__(self, use_cloud: bool = False):
        """Initialize with local or cloud configuration"""
        self.use_cloud = use_cloud
        self.db_config = config.CLOUD_CONFIG if use_cloud else config.LOCAL_CONFIG
        self.client = None
        self.sys_db = None
        self.databases = {}
        self.arango_rdf_instances = {}
        
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
            self.sys_db.version()
            logger.info("Successfully connected to ArangoDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            return False
    
    def load_foaf_data_with_ontology(self) -> Optional[Graph]:
        """Load both FOAF ontology and data into a single graph"""
        try:
            logger.info("Loading FOAF ontology and data...")
            foaf_graph = Graph()
            
            # Load the FOAF ontology first
            ontology_path = os.path.expanduser(config.DATA_PATHS["foaf_ontology"])
            if not Path(ontology_path).exists():
                logger.error(f"FOAF ontology file not found: {ontology_path}")
                return None
            
            # Try different formats for ontology
            formats_to_try = ["xml", "turtle", "n3", "nt"]
            loaded = False
            for fmt in formats_to_try:
                try:
                    logger.info(f"Trying to load ontology with format: {fmt}")
                    foaf_graph.parse(ontology_path, format=fmt)
                    loaded = True
                    logger.info(f"Successfully loaded ontology using {fmt} format")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load ontology as {fmt}: {e}")
                    continue
            
            if not loaded:
                logger.error("Failed to load ontology in any format")
                return None
                
            ontology_triples = len(foaf_graph)
            logger.info(f"Loaded {ontology_triples} ontology triples")
            
            # Load the FOAF data
            data_path = os.path.expanduser(config.DATA_PATHS["foaf_data"])
            if not Path(data_path).exists():
                logger.error(f"FOAF data file not found: {data_path}")
                return None
                
            foaf_graph.parse(data_path, format="turtle")
            total_triples = len(foaf_graph)
            data_triples = total_triples - ontology_triples
            
            logger.info(f"Loaded {data_triples} data triples")
            logger.info(f"Total: {total_triples} RDF triples (ontology + data)")
            
            return foaf_graph
            
        except Exception as e:
            logger.error(f"Failed to load FOAF data: {e}")
            return None
    
    def drop_pgt_databases(self) -> bool:
        """Drop existing PGT databases"""
        try:
            pgt_db_names = ["pgt", "pgt_node"]
            
            for model_type in pgt_db_names:
                db_name = config.DATABASE_NAMES[model_type]
                
                if self.sys_db.has_database(db_name):
                    logger.info(f"Dropping existing database: {db_name}")
                    self.sys_db.delete_database(db_name)
                else:
                    logger.info(f"Database {db_name} doesn't exist, skipping drop")
                    
            logger.info("PGT databases dropped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop PGT databases: {e}")
            return False
    
    def create_pgt_databases(self) -> bool:
        """Create fresh PGT databases"""
        try:
            pgt_db_names = ["pgt", "pgt_node"]
            
            for model_type in pgt_db_names:
                db_name = config.DATABASE_NAMES[model_type]
                logger.info(f"Creating database: {db_name}")
                
                # Create new database
                self.sys_db.create_database(db_name)
                
                # Connect to the new database
                db = self.client.db(
                    db_name,
                    username=self.db_config["username"],
                    password=self.db_config["password"]
                )
                
                self.databases[model_type] = db
                self.arango_rdf_instances[model_type] = ArangoRDF(db)
                
            logger.info("PGT databases created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PGT databases: {e}")
            return False
    
    def load_pgt_model_with_context(self, foaf_graph: Graph) -> bool:
        """Load data using PGT with contextualize_graph=True"""
        try:
            logger.info("Loading data using PGT model with contextualize_graph=True...")
            arango_rdf = self.arango_rdf_instances["pgt"]
            
            # PGT with contextualization to handle missing ontologies
            arango_rdf.rdf_to_arangodb_by_pgt(
                name=config.GRAPH_NAMES["pgt"],
                rdf_graph=foaf_graph,
                overwrite_graph=True,
                contextualize_graph=True  # This should fix the UnknownResource issue
            )
            
            logger.info("PGT model loaded successfully with contextualization")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PGT model: {e}")
            return False
    
    def load_pgt_node_model_with_context(self, foaf_graph: Graph) -> bool:
        """Load data using PGT-Node with contextualize_graph=True and resource_collection_name='Node'"""
        try:
            logger.info("Loading data using PGT-Node model with contextualize_graph=True and resource_collection_name='Node'...")
            arango_rdf = self.arango_rdf_instances["pgt_node"]
            
            # PGT-Node with contextualization and Node collection
            arango_rdf.rdf_to_arangodb_by_pgt(
                name=config.GRAPH_NAMES["pgt_node"],
                rdf_graph=foaf_graph,
                overwrite_graph=True,
                contextualize_graph=True,  # This should fix the UnknownResource issue
                resource_collection_name="Node"  # This will put all vertices in a "Node" collection
            )
            
            logger.info("PGT-Node model loaded successfully with contextualization and Node collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PGT-Node model: {e}")
            return False
    
    def print_database_stats(self):
        """Print statistics for the recreated databases"""
        logger.info("\n" + "="*60)
        logger.info("UPDATED DATABASE STATISTICS")
        logger.info("="*60)
        
        for model_type, db in self.databases.items():
            db_name = config.DATABASE_NAMES[model_type]
            logger.info(f"\n{db_name} ({model_type.upper()}):")
            logger.info("-" * 40)
            
            try:
                # Get collections
                collections = db.collections()
                vertex_collections = [c for c in collections if not c['name'].startswith('_') and not c['name'].endswith('_edge')]
                edge_collections = [c for c in collections if c['name'].endswith('_edge') or c['type'] == 3]
                
                logger.info(f"Vertex Collections: {len(vertex_collections)}")
                for col in vertex_collections:
                    count = db.collection(col['name']).count()
                    logger.info(f"  - {col['name']}: {count} documents")
                
                logger.info(f"Edge Collections: {len(edge_collections)}")
                for col in edge_collections:
                    count = db.collection(col['name']).count()
                    logger.info(f"  - {col['name']}: {count} documents")
                    
                # Check for UnknownResource collections
                unknown_cols = [c for c in vertex_collections if 'UnknownResource' in c['name']]
                if unknown_cols:
                    logger.warning(f"Still found {len(unknown_cols)} UnknownResource collections:")
                    for col in unknown_cols:
                        count = db.collection(col['name']).count()
                        logger.warning(f"  - {col['name']}: {count} documents")
                else:
                    logger.info("✅ No UnknownResource collections found!")
                    
            except Exception as e:
                logger.error(f"Error getting stats for {db_name}: {e}")
    
    def fix_pgt_databases(self) -> bool:
        """Run the PGT-Node database fix only"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("FIXING PGT-NODE FOAF DATABASES ONLY")
        logger.info("="*60)
        
        # Step 1: Connect to ArangoDB
        if not self.connect_to_arango():
            return False
        
        # Step 2: Load FOAF data with ontology
        foaf_graph = self.load_foaf_data_with_ontology()
        if foaf_graph is None:
            return False
        
        # Step 3: Drop existing PGT-Node database only
        try:
            db_name = config.DATABASE_NAMES["pgt_node"]
            if self.sys_db.has_database(db_name):
                logger.info(f"Dropping existing database: {db_name}")
                self.sys_db.delete_database(db_name)
            else:
                logger.info(f"Database {db_name} doesn't exist, skipping drop")
        except Exception as e:
            logger.error(f"Failed to drop PGT-Node database: {e}")
            return False
        
        # Step 4: Create fresh PGT-Node database only
        try:
            model_type = "pgt_node"
            db_name = config.DATABASE_NAMES[model_type]
            logger.info(f"Creating database: {db_name}")
            
            # Create new database
            self.sys_db.create_database(db_name)
            
            # Connect to the new database
            db = self.client.db(
                db_name,
                username=self.db_config["username"],
                password=self.db_config["password"]
            )
            
            self.databases[model_type] = db
            self.arango_rdf_instances[model_type] = ArangoRDF(db)
            
            logger.info("PGT-Node database created successfully")
        except Exception as e:
            logger.error(f"Failed to create PGT-Node database: {e}")
            return False
        
        # Step 5: Load PGT-Node model with contextualization and Node collection
        if not self.load_pgt_node_model_with_context(foaf_graph):
            return False
        
        # Step 6: Print updated statistics
        self.print_database_stats()
        
        elapsed_time = time.time() - start_time
        logger.info(f"\nPGT-Node database fix completed successfully in {elapsed_time:.2f} seconds")
        
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix PGT FOAF Databases with Contextualization")
    parser.add_argument(
        "--cloud", 
        action="store_true", 
        help="Use cloud ArangoDB instance instead of local"
    )
    
    args = parser.parse_args()
    
    if args.cloud and not config.CLOUD_CONFIG["password"]:
        logger.error("Cloud password not set. Please set ARANGO_CLOUD_PASSWORD environment variable.")
        sys.exit(1)
    
    fixer = FOAFPGTFixer(use_cloud=args.cloud)
    
    if fixer.fix_pgt_databases():
        logger.info("\nPGT databases fixed successfully!")
        logger.info("The UnknownResource collections should now be resolved.")
        logger.info("You can run query_demo.py to test the updated databases.")
    else:
        logger.error("Failed to fix PGT databases!")
        sys.exit(1)


if __name__ == "__main__":
    main() 