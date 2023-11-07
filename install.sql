-- MySQL dump 10.13  Distrib 5.6.50, for Linux (x86_64)
--
-- Host: localhost    Database: ml
-- ------------------------------------------------------
-- Server version	5.6.50-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `cloud_black`
--

DROP TABLE IF EXISTS `cloud_black`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_black` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(20) NOT NULL,
  `enable` tinyint(1) NOT NULL DEFAULT '1',
  `addtime` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cloud_black`
--

LOCK TABLES `cloud_black` WRITE;
/*!40000 ALTER TABLE `cloud_black` DISABLE KEYS */;
/*!40000 ALTER TABLE `cloud_black` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cloud_config`
--

DROP TABLE IF EXISTS `cloud_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_config` (
  `key` varchar(32) NOT NULL,
  `value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cloud_config`
--

LOCK TABLES `cloud_config` WRITE;
/*!40000 ALTER TABLE `cloud_config` DISABLE KEYS */;
INSERT INTO `cloud_config` VALUES ('admin_password','baixinyi520.'),('admin_username','linke'),('bt_key',''),('bt_surl',''),('bt_type','0'),('bt_url',''),('download_page','1'),('new_version','8.0.3'),('new_version_btm','2.2.9'),('new_version_win','7.9.0'),('syskey','aa393k9z9679yy3A'),('updateall_type','0'),('updateall_type_win','0'),('update_date','2023-10-08'),('update_date_btm','2023-08-11'),('update_date_win','2023-07-20'),('update_msg','暂无更新日志'),('update_msg_btm','暂无更新日志'),('update_msg_win','暂无更新日志'),('whitelist','0');
/*!40000 ALTER TABLE `cloud_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cloud_log`
--

DROP TABLE IF EXISTS `cloud_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` tinyint(4) NOT NULL DEFAULT '1',
  `action` varchar(40) NOT NULL,
  `data` varchar(150) DEFAULT NULL,
  `addtime` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=262 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cloud_log`
--

LOCK TABLES `cloud_log` WRITE;
/*!40000 ALTER TABLE `cloud_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `cloud_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cloud_record`
--

DROP TABLE IF EXISTS `cloud_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(20) NOT NULL,
  `addtime` datetime NOT NULL,
  `usetime` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cloud_record`
--

LOCK TABLES `cloud_record` WRITE;
/*!40000 ALTER TABLE `cloud_record` DISABLE KEYS */;
/*!40000 ALTER TABLE `cloud_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cloud_white`
--

DROP TABLE IF EXISTS `cloud_white`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_white` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(20) NOT NULL,
  `enable` tinyint(1) NOT NULL DEFAULT '1',
  `addtime` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cloud_white`
--

LOCK TABLES `cloud_white` WRITE;
/*!40000 ALTER TABLE `cloud_white` DISABLE KEYS */;
/*!40000 ALTER TABLE `cloud_white` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'ml'
--

--
-- Dumping routines for database 'ml'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-11-07 13:31:13
