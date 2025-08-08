#!/usr/bin/env python3
"""
Shared database utilities for the FOAF demonstration project.
Eliminates code duplication across database connection and management.

Author: Arthur Keen
Date: January 2025
"""

import logging
from typing import Dict, Optional
from arango import ArangoClient
from arango_rdf import ArangoRDF
import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database connection and management"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize database manager with configuration
        
        Args:
            db_config: Database configuration dictionary
        """
        self.db_config = db_config
        self.client = None
        self.sys_db = None
        
    def get_client(self) -> ArangoClient:
        """
        Get or create ArangoDB client
        
        Returns:
            ArangoClient instance
        """
        if self.client is None:
            self.client = ArangoClient(hosts=self.db_config["host"])
        return self.client
        
    def connect_to_system_db(self):
        """
        Connect to _system database
        
        Returns:
            Database instance for _system
            
        Raises:
            Exception: If connection fails
        """
        try:
            client = self.get_client()
            self.sys_db = client.db(
                "_system",
                username=self.db_config["username"],
                password=self.db_config["password"]
            )
            
            version_info = self.sys_db.version()
            logger.info(f"Successfully connected to ArangoDB {version_info}")
            return self.sys_db
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            raise
            
    def connect_to_database(self, db_name: str):
        """
        Connect to a specific database
        
        Args:
            db_name: Name of the database to connect to
            
        Returns:
            Database instance
            
        Raises:
            Exception: If connection fails
        """
        try:
            client = self.get_client()
            db = client.db(
                db_name,
                username=self.db_config["username"],
                password=self.db_config["password"]
            )
            logger.debug(f"Connected to database: {db_name}")
            return db
            
        except Exception as e:
            logger.error(f"Failed to connect to database {db_name}: {e}")
            raise
            
    def create_database_if_not_exists(self, db_name: str):
        """
        Create database if it doesn't exist, then connect to it
        
        Args:
            db_name: Name of the database to create/connect
            
        Returns:
            Database instance
            
        Raises:
            Exception: If creation or connection fails
        """
        try:
            if self.sys_db is None:
                self.connect_to_system_db()
                
            # Check if database exists
            if not self.sys_db.has_database(db_name):
                logger.info(f"Creating database: {db_name}")
                self.sys_db.create_database(db_name)
            else:
                logger.info(f"Database {db_name} already exists")
                
            return self.connect_to_database(db_name)
            
        except Exception as e:
            logger.error(f"Failed to create/connect to database {db_name}: {e}")
            raise
            
    def recreate_database(self, db_name: str):
        """
        Drop and recreate a database
        
        Args:
            db_name: Name of the database to recreate
            
        Returns:
            Database instance
            
        Raises:
            Exception: If recreation fails
        """
        try:
            if self.sys_db is None:
                self.connect_to_system_db()
                
            # Drop existing database if it exists
            if self.sys_db.has_database(db_name):
                logger.info(f"Dropping existing database: {db_name}")
                self.sys_db.delete_database(db_name)
                
            # Create new database
            logger.info(f"Creating database: {db_name}")
            self.sys_db.create_database(db_name)
            
            return self.connect_to_database(db_name)
            
        except Exception as e:
            logger.error(f"Failed to recreate database {db_name}: {e}")
            raise
            
    def get_arango_rdf(self, database) -> ArangoRDF:
        """
        Create ArangoRDF instance for a database
        
        Args:
            database: Database instance
            
        Returns:
            ArangoRDF instance
        """
        return ArangoRDF(database)
        
    def connect_to_all_foaf_databases(self) -> Dict[str, object]:
        """
        Connect to all FOAF databases
        
        Returns:
            Dictionary mapping model type to database instance
            
        Raises:
            Exception: If any connection fails
        """
        databases = {}
        
        for model_type, db_name in config.DATABASE_NAMES.items():
            logger.info(f"Connecting to {db_name}...")
            databases[model_type] = self.connect_to_database(db_name)
            
        logger.info("Successfully connected to all FOAF databases")
        return databases


class LocalDatabaseManager(DatabaseManager):
    """Database manager for local development"""
    
    def __init__(self):
        super().__init__(config.LOCAL_CONFIG)


class CloudDatabaseManager(DatabaseManager):
    """Database manager for cloud deployment"""
    
    def __init__(self):
        super().__init__(config.CLOUD_CONFIG)


def get_database_manager(use_cloud: bool = False) -> DatabaseManager:
    """
    Factory function to get appropriate database manager
    
    Args:
        use_cloud: Whether to use cloud configuration
        
    Returns:
        DatabaseManager instance
    """
    if use_cloud:
        return CloudDatabaseManager()
    else:
        return LocalDatabaseManager()
