-- MySQL dump 10.13  Distrib 5.5.62, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: sqa_collector
-- ------------------------------------------------------
-- Server version	5.5.62-0ubuntu0.12.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `sqa_collector`
--

DROP TABLE IF EXISTS `sqa_collector`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sqa_collector` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `started` datetime NOT NULL,
  `ended` datetime DEFAULT NULL,
  `raised_by` varchar(45) NOT NULL DEFAULT 'unknown',
  `afi` enum('ipv4','ipv6') NOT NULL DEFAULT 'ipv4',
  `short` varchar(100) DEFAULT NULL,
  `long` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1556645 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sqa_collector_correlator`
--

DROP TABLE IF EXISTS `sqa_collector_correlator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sqa_collector_correlator` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `collector_id` int(11) NOT NULL,
  `correlator_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `collector_correlator_idx` (`collector_id`,`correlator_id`),
  KEY `collector_idx` (`collector_id`),
  KEY `sqa_correlator_id_idx` (`correlator_id`),
  CONSTRAINT `sqa_collector_id` FOREIGN KEY (`collector_id`) REFERENCES `sqa_collector` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=489020 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sqa_correlator`
--

DROP TABLE IF EXISTS `sqa_correlator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sqa_correlator` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10864 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sqa_correlator_objects`
--

DROP TABLE IF EXISTS `sqa_correlator_objects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sqa_correlator_objects` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sqa_correlator_id` int(11) NOT NULL,
  `object` varchar(45) NOT NULL,
  `percentage` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `sqa_correlator_id_idx` (`sqa_correlator_id`),
  CONSTRAINT `sqa_correlator_id` FOREIGN KEY (`sqa_correlator_id`) REFERENCES `sqa_correlator` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19857 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-25 15:43:16
