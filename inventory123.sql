CREATE DATABASE  IF NOT EXISTS `inventory123` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `inventory123`;
-- MySQL dump 10.13  Distrib 8.0.24, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: inventory123
-- ------------------------------------------------------
-- Server version	8.0.24

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `catalogue`
--

DROP TABLE IF EXISTS `catalogue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `catalogue` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sku` varchar(11) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `product_description` varchar(1000) DEFAULT 'no informations found for this product',
  `product_model` varchar(45) DEFAULT NULL,
  `brand` varchar(255) DEFAULT NULL,
  `category` varchar(45) DEFAULT NULL,
  `price` float DEFAULT NULL,
  `sale_price` float DEFAULT NULL,
  `quantity` varchar(45) DEFAULT NULL,
  `condition` varchar(45) DEFAULT NULL,
  `upc` varchar(255) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `product_image` varchar(45) DEFAULT 'default_product.png',
  `user_id` int NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_product_idx` (`user_id`),
  CONSTRAINT `user_product` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `catalogue`
--

LOCK TABLES `catalogue` WRITE;
/*!40000 ALTER TABLE `catalogue` DISABLE KEYS */;
INSERT INTO `catalogue` VALUES (1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','Product-49-brashka','brashka','electonric',388,358,'38','TRUE','UPC-49-brashka','usa','default_product.png',12,'2023-02-28 05:48:12','2023-05-09 02:11:18'),(6,'q1','qwq','qqqqqqqqqqqqqqq','qwqwqw','qqqqqqqqqqqqqqqq','qqqqqqqqqqqqqqqq',30,0,'1','qwqw','qwqw','qwq','default_product.png',12,'2023-03-01 23:03:55','2023-04-02 12:42:31'),(8,'qwxwq','xqwxw','','wd','xwq','wq',10,20,'12','wdqw','dqwd','dwq','default_product.png',12,'2023-03-06 07:22:15',NULL),(9,'qwxwq12','xqwxw','','wd','xwq','wq',0.21,20,'12','wdqw','dqwd','dwq','default_product.png',12,'2023-03-06 07:22:24','2023-04-02 15:25:55'),(10,'abc5ga12','test1','','test','test barnd','test catagory',30,8,'10','true','some test','egypt','default_product.png',12,'2023-03-06 07:34:03','2023-03-06 07:34:52'),(11,'aa','aa','aa','a','a','a',10,8,'1','cp','yes','egypt','default_product.png',3,'2023-03-08 20:47:46',NULL),(12,'PRO1001','mobile','mobile it have brand : brashka and it\'s from catgory of electonric, the price of it is 150 but sale price is 140, sku: PRO1001','Product-17-brashka','brashka','electonric',150,140,'17','FALSE','UPC-17-brashka','china','default_product.png',12,'2023-04-02 13:39:20','2023-04-02 16:49:01'),(13,'PRO1002','robot ix1','robot ix1 it have brand : brashka and it\'s from catgory of electonric, the price of it is 100 but sale price is 90, sku: PRO1002','Product-19-brashka','brashka','electonric',100,90,'19','FALSE','UPC-19-brashka','russia','default_product.png',12,'2023-04-02 13:39:21','2023-04-02 16:49:01'),(14,'PRO1003','robot iv2','robot iv2 it have brand : h&m and it\'s from catgory of electonric, the price of it is 150 but sale price is 140, sku: PRO1003','Product-19-h&m','h&m','electonric',150,140,'19','TRUE','UPC-19-h&m','canda','default_product.png',12,'2023-04-02 13:39:21','2023-04-02 16:49:02'),(15,'PRO1004','robot aram','robot aram it have brand : h&m and it\'s from catgory of electonric, the price of it is 10 but sale price is 8, sku: PRO1004','Product-5-h&m','h&m','electonric',10,8,'5','FALSE','UPC-5-h&m','egypt','default_product.png',12,'2023-04-02 13:39:21','2023-05-08 05:48:15'),(16,'PRO1005','alaram','alaram it have brand : brashka and it\'s from catgory of electonric, the price of it is 50 but sale price is 40, sku: PRO1005','Product-12-brashka','brashka','electonric',50,40,'12','FALSE','UPC-12-brashka','egypt','default_product.png',12,'2023-04-02 13:39:21','2023-04-02 16:49:02'),(17,'PRO1006','washmachine','washmachine it have brand : h&m and it\'s from catgory of electonric, the price of it is 600 but sale price is 500, sku: PRO1006','Product-33-h&m','h&m','electonric',600,500,'32','TRUE','UPC-33-h&m','india','default_product.png',12,'2023-04-02 13:39:21','2023-05-08 05:36:53'),(18,'PRO1007','catwalker','catwalker it have brand : h&m and it\'s from catgory of transportation, the price of it is 2000 but sale price is 1500, sku: PRO1007','Product-22-h&m','h&m','transportation',2000,1500,'22','TRUE','UPC-22-h&m','usa','default_product.png',12,'2023-04-02 13:39:21','2023-04-02 16:49:02'),(19,'PRO1008','bike','bike it have brand : brashka and it\'s from catgory of transportation, the price of it is 200 but sale price is 150, sku: PRO1008','Product-39-brashka','brashka','transportation',200,150,'39','FALSE','UPC-39-brashka','colmbia','default_product.png',12,'2023-04-02 13:39:22','2023-04-02 16:49:02'),(20,'PRO1009','motor','motor it have brand : h&m and it\'s from catgory of components, the price of it is 2 but sale price is 1, sku: PRO1009','Product-24-h&m','h&m','components',2,1,'24','FALSE','UPC-24-h&m','canda','default_product.png',12,'2023-04-02 13:39:22','2023-04-02 16:49:02'),(21,'PRO1010','dc motor v2','dc motor v2 it have brand : brashka and it\'s from catgory of components, the price of it is 5 but sale price is 4, sku: PRO1010','Product-37-brashka','brashka','components',5,4,'37','TRUE','UPC-37-brashka','colmbia','default_product.png',12,'2023-04-02 13:39:22','2023-04-08 23:17:13'),(22,'PRO1011','raspary pi 4','raspary pi 4 it have brand : h&m and it\'s from catgory of components, the price of it is 300 but sale price is 299, sku: PRO1011','Product-24-h&m','h&m','components',300,299,'24','TRUE','UPC-24-h&m','canda','default_product.png',12,'2023-04-02 13:39:22','2023-04-08 23:17:13'),(23,'PRO1012','raspary pi 3','raspary pi 3 it have brand : h&m and it\'s from catgory of components, the price of it is 250 but sale price is 249, sku: PRO1012','Product-0-h&m','h&m','components',250,249,'0','FALSE','UPC-0-h&m','uae','default_product.png',12,'2023-04-02 13:39:22','2023-04-08 23:17:13'),(24,'PRO1013','arduino','arduino it have brand : brashka and it\'s from catgory of components, the price of it is 70 but sale price is 1, sku: PRO1013','Product-33-brashka','brashka','components',70,1,'33','TRUE','UPC-33-brashka','russia','default_product.png',12,'2023-04-02 13:39:22','2023-04-08 23:17:13'),(25,'PRO1014','whale','whale it have brand : brashka and it\'s from catgory of components, the price of it is 0.2 but sale price is 0.1, sku: PRO1014','Product-40-brashka','brashka','components',0.2,0.1,'40','FALSE','UPC-40-brashka','colmbia','default_product.png',12,'2023-04-02 13:39:22','2023-04-08 23:17:13'),(26,'PRO1015','hat','hat it have brand : h&m and it\'s from catgory of clothes, the price of it is 2 but sale price is 1, sku: PRO1015','Product-32-h&m','h&m','clothes',2,1,'32','FALSE','UPC-32-h&m','usa','default_product.png',12,'2023-04-02 13:39:23','2023-04-08 23:17:14'),(27,'PRO1016','helemt','helemt it have brand : h&m and it\'s from catgory of clothes, the price of it is 4 but sale price is 3, sku: PRO1016','Product-41-h&m','h&m','clothes',4,3,'41','FALSE','UPC-41-h&m','colmbia','default_product.png',12,'2023-04-02 13:39:23','2023-04-08 23:17:14'),(28,'PRO1017','power supply','power supply it have brand : brashka and it\'s from catgory of components, the price of it is 30 but sale price is 25, sku: PRO1017','Product-31-brashka','brashka','components',30,25,'31','FALSE','UPC-31-brashka','colmbia','default_product.png',12,'2023-04-02 13:39:23','2023-04-08 23:17:14'),(29,'PRO1018','ultra sonic sensor','ultra sonic sensor it have brand : brashka and it\'s from catgory of components, the price of it is 3 but sale price is 2, sku: PRO1018','Product-42-brashka','brashka','components',3,2,'42','FALSE','UPC-42-brashka','canda','default_product.png',12,'2023-04-02 13:39:23','2023-04-08 23:17:14'),(30,'PRO1019','heartbeat sensor','heartbeat sensor it have brand : h&m and it\'s from catgory of components, the price of it is 3 but sale price is 2, sku: PRO1019','Product-13-h&m','h&m','components',3,2,'13','TRUE','UPC-13-h&m','canda','default_product.png',12,'2023-04-02 13:39:23','2023-04-08 23:17:14'),(31,'PRO1020','resestors','resestors it have brand : brashka and it\'s from catgory of components, the price of it is 5 but sale price is 1, sku: PRO1020','Product-23-brashka','brashka','components',5,1,'23','FALSE','UPC-23-brashka','german','default_product.png',12,'2023-04-02 13:39:23','2023-04-08 23:17:15'),(32,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','Product-49-brashka','brashka','electonric',388,358,'49','TRUE','UPC-49-brashka','usa','default_product.png',12,'2023-04-02 16:22:35',NULL),(33,'PRO1001','mobile','mobile it have brand : brashka and it\'s from catgory of electonric, the price of it is 150 but sale price is 140, sku: PRO1001','Product-17-brashka','brashka','electonric',150,140,'17','FALSE','UPC-17-brashka','china','default_product.png',12,'2023-04-02 16:22:35',NULL),(34,'PRO1002','robot ix1','robot ix1 it have brand : brashka and it\'s from catgory of electonric, the price of it is 100 but sale price is 90, sku: PRO1002','Product-19-brashka','brashka','electonric',100,90,'19','FALSE','UPC-19-brashka','russia','default_product.png',12,'2023-04-02 16:22:35',NULL),(35,'PRO1003','robot iv2','robot iv2 it have brand : h&m and it\'s from catgory of electonric, the price of it is 150 but sale price is 140, sku: PRO1003','Product-19-h&m','h&m','electonric',150,140,'19','TRUE','UPC-19-h&m','canda','default_product.png',12,'2023-04-02 16:22:35',NULL),(36,'PRO1004','robot aram','robot aram it have brand : h&m and it\'s from catgory of electonric, the price of it is 10 but sale price is 8, sku: PRO1004','Product-5-h&m','h&m','electonric',10,8,'5','FALSE','UPC-5-h&m','egypt','default_product.png',12,'2023-04-02 16:22:35',NULL),(37,'PRO1005','alaram','alaram it have brand : brashka and it\'s from catgory of electonric, the price of it is 50 but sale price is 40, sku: PRO1005','Product-12-brashka','brashka','electonric',50,40,'12','FALSE','UPC-12-brashka','egypt','default_product.png',12,'2023-04-02 16:22:35',NULL),(38,'PRO1006','washmachine','washmachine it have brand : h&m and it\'s from catgory of electonric, the price of it is 600 but sale price is 500, sku: PRO1006','Product-33-h&m','h&m','electonric',600,500,'33','TRUE','UPC-33-h&m','india','default_product.png',12,'2023-04-02 16:22:35',NULL),(39,'PRO1007','catwalker','catwalker it have brand : h&m and it\'s from catgory of transportation, the price of it is 2000 but sale price is 1500, sku: PRO1007','Product-22-h&m','h&m','transportation',2000,1500,'22','TRUE','UPC-22-h&m','usa','default_product.png',12,'2023-04-02 16:22:35',NULL),(40,'PRO1008','bike','bike it have brand : brashka and it\'s from catgory of transportation, the price of it is 200 but sale price is 150, sku: PRO1008','Product-39-brashka','brashka','transportation',200,150,'39','FALSE','UPC-39-brashka','colmbia','default_product.png',12,'2023-04-02 16:22:35',NULL),(41,'PRO1009','motor','motor it have brand : h&m and it\'s from catgory of components, the price of it is 2 but sale price is 1, sku: PRO1009','Product-24-h&m','h&m','components',2,1,'24','FALSE','UPC-24-h&m','canda','default_product.png',12,'2023-04-02 16:22:35',NULL),(42,'PRO1010','dc motor v2','dc motor v2 it have brand : brashka and it\'s from catgory of components, the price of it is 5 but sale price is 4, sku: PRO1010','Product-37-brashka','brashka','components',5,4,'37','TRUE','UPC-37-brashka','colmbia','default_product.png',12,'2023-04-02 16:22:35',NULL),(43,'PRO1011','raspary pi 4','raspary pi 4 it have brand : h&m and it\'s from catgory of components, the price of it is 300 but sale price is 299, sku: PRO1011','Product-24-h&m','h&m','components',300,299,'24','TRUE','UPC-24-h&m','canda','default_product.png',12,'2023-04-02 16:22:35',NULL),(44,'PRO1012','raspary pi 3','raspary pi 3 it have brand : h&m and it\'s from catgory of components, the price of it is 250 but sale price is 249, sku: PRO1012','Product-0-h&m','h&m','components',250,249,'0','FALSE','UPC-0-h&m','uae','default_product.png',12,'2023-04-02 16:22:35',NULL),(45,'PRO1013','arduino','arduino it have brand : brashka and it\'s from catgory of components, the price of it is 70 but sale price is 1, sku: PRO1013','Product-33-brashka','brashka','components',70,1,'33','TRUE','UPC-33-brashka','russia','default_product.png',12,'2023-04-02 16:22:35',NULL),(46,'PRO1014','whale','whale it have brand : brashka and it\'s from catgory of components, the price of it is 0.2 but sale price is 0.1, sku: PRO1014','Product-40-brashka','brashka','components',0.2,0.1,'40','FALSE','UPC-40-brashka','colmbia','default_product.png',12,'2023-04-02 16:22:35',NULL),(47,'PRO1015','hat','hat it have brand : h&m and it\'s from catgory of clothes, the price of it is 2 but sale price is 1, sku: PRO1015','Product-32-h&m','h&m','clothes',2,1,'32','FALSE','UPC-32-h&m','usa','default_product.png',12,'2023-04-02 16:22:35',NULL),(48,'PRO1016','helemt','helemt it have brand : h&m and it\'s from catgory of clothes, the price of it is 4 but sale price is 3, sku: PRO1016','Product-41-h&m','h&m','clothes',4,3,'41','FALSE','UPC-41-h&m','colmbia','default_product.png',12,'2023-04-02 16:22:35',NULL),(49,'PRO1017','power supply','power supply it have brand : brashka and it\'s from catgory of components, the price of it is 30 but sale price is 25, sku: PRO1017','Product-31-brashka','brashka','components',30,25,'31','FALSE','UPC-31-brashka','colmbia','default_product.png',12,'2023-04-02 16:22:35',NULL),(50,'PRO1018','ultra sonic sensor','ultra sonic sensor it have brand : brashka and it\'s from catgory of components, the price of it is 3 but sale price is 2, sku: PRO1018','Product-42-brashka','brashka','components',3,2,'42','FALSE','UPC-42-brashka','canda','default_product.png',12,'2023-04-02 16:22:35',NULL),(51,'PRO1020','resestors','resestors it have brand : brashka and it\'s from catgory of components, the price of it is 5 but sale price is 1, sku: PRO1020','Product-23-brashka','brashka','components',5,1,'23','FALSE','UPC-23-brashka','german','default_product.png',12,'2023-04-02 16:22:35',NULL),(52,'PRO1022','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','Product-49-brashka','brashka','electonric',388,358,'49','TRUE','UPC-49-brashka','usa','default_product.png',12,'2023-04-08 23:17:10',NULL),(53,'PRO1023','mobile','mobile it have brand : brashka and it\'s from catgory of electonric, the price of it is 150 but sale price is 140, sku: PRO1001','Product-17-brashka','brashka','electonric',150,140,'17','FALSE','UPC-17-brashka','china','default_product.png',12,'2023-04-08 23:17:11',NULL),(54,'PRO1024','robot ix1','robot ix1 it have brand : brashka and it\'s from catgory of electonric, the price of it is 100 but sale price is 90, sku: PRO1002','Product-19-brashka','brashka','electonric',100,90,'19','FALSE','UPC-19-brashka','russia','default_product.png',12,'2023-04-08 23:17:11',NULL),(55,'PRO1025','robot iv2','robot iv2 it have brand : h&m and it\'s from catgory of electonric, the price of it is 150 but sale price is 140, sku: PRO1003','Product-19-h&m','h&m','electonric',150,140,'19','TRUE','UPC-19-h&m','canda','default_product.png',12,'2023-04-08 23:17:11',NULL),(56,'PRO1026','robot aram','robot aram it have brand : h&m and it\'s from catgory of electonric, the price of it is 10 but sale price is 8, sku: PRO1004','Product-5-h&m','h&m','electonric',10,8,'5','FALSE','UPC-5-h&m','egypt','default_product.png',12,'2023-04-08 23:17:11',NULL),(57,'PRO1027','alaram','alaram it have brand : brashka and it\'s from catgory of electonric, the price of it is 50 but sale price is 40, sku: PRO1005','Product-12-brashka','brashka','electonric',50,40,'12','FALSE','UPC-12-brashka','egypt','default_product.png',12,'2023-04-08 23:17:11',NULL),(58,'PRO1028','washmachine','washmachine it have brand : h&m and it\'s from catgory of electonric, the price of it is 600 but sale price is 500, sku: PRO1006','Product-33-h&m','h&m','electonric',600,500,'33','TRUE','UPC-33-h&m','india','default_product.png',12,'2023-04-08 23:17:12',NULL),(59,'PRO1029','catwalker','catwalker it have brand : h&m and it\'s from catgory of transportation, the price of it is 2000 but sale price is 1500, sku: PRO1007','Product-22-h&m','h&m','transportation',2000,1500,'22','TRUE','UPC-22-h&m','usa','default_product.png',12,'2023-04-08 23:17:12',NULL),(60,'PRO1030','bike','bike it have brand : brashka and it\'s from catgory of transportation, the price of it is 200 but sale price is 150, sku: PRO1008','Product-39-brashka','brashka','transportation',200,150,'39','FALSE','UPC-39-brashka','colmbia','default_product.png',12,'2023-04-08 23:17:12',NULL),(61,'PRO1031','motor','motor it have brand : h&m and it\'s from catgory of components, the price of it is 2 but sale price is 1, sku: PRO1009','Product-24-h&m','h&m','components',2,1,'24','FALSE','UPC-24-h&m','canda','default_product.png',12,'2023-04-08 23:17:12',NULL),(62,'anudq1234','helloworld','hi','something','yes','newone',2,1.01,'1','true','123','test','default_product.png',12,'2023-05-09 02:17:27',NULL);
/*!40000 ALTER TABLE `catalogue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dashboard`
--

DROP TABLE IF EXISTS `dashboard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dashboard` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(45) DEFAULT 'New Dashboard',
  `num_of_listings` int DEFAULT '0',
  `num_of_orders` int DEFAULT '0',
  `sum_of_monthly_purchases` decimal(12,2) DEFAULT '0.00',
  `default` tinyint DEFAULT '0',
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_dashboard_idx` (`user_id`),
  CONSTRAINT `user_dashboard` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dashboard`
--

LOCK TABLES `dashboard` WRITE;
/*!40000 ALTER TABLE `dashboard` DISABLE KEYS */;
INSERT INTO `dashboard` VALUES (2,3,'test1',0,0,0.00,1,'2023-02-27 23:42:26','2023-05-06 10:36:44'),(3,12,'First Dashboard',0,0,0.00,1,'2023-02-28 04:58:06','2023-05-08 07:18:31'),(5,12,'test11',3,0,0.00,0,'2023-02-28 21:32:22','2023-05-08 07:03:27'),(6,12,'test',0,0,0.00,0,'2023-03-01 01:42:59','2023-05-08 07:18:30'),(7,12,'New Dashboard',0,0,0.00,0,'2023-03-01 02:56:47',NULL),(8,12,'New Dashboard',1,1,10.01,0,'2023-03-01 03:05:16',NULL),(10,12,'New Dashboard',0,0,0.00,0,'2023-03-01 21:51:17',NULL),(11,12,'New Dashboard',0,0,0.00,0,'2023-03-01 22:33:18',NULL),(14,12,'New Dashboard',0,0,0.00,0,'2023-03-04 02:17:04',NULL),(15,12,'New Dashboard',0,0,0.00,0,'2023-03-04 02:17:44',NULL),(16,12,'New Dashboard',0,0,0.00,0,'2023-03-04 02:18:10',NULL),(17,12,'test',0,0,0.00,0,'2023-03-04 02:18:29',NULL),(18,12,'New Dashboard2',0,0,0.00,0,'2023-03-04 02:19:48',NULL),(19,12,'Test add new Dashboard',0,0,0.00,0,'2023-03-06 07:31:23',NULL),(20,12,'New Dashboard1',10,20,1.00,0,'2023-03-08 20:10:03',NULL),(21,12,'test123',0,0,0.00,0,'2023-04-08 14:02:36',NULL),(22,12,'test12312',0,0,0.00,0,'2023-04-08 14:10:33',NULL),(23,12,'New Dashboard12',0,0,0.00,0,'2023-04-08 14:27:22',NULL),(24,12,'hello',0,0,0.00,0,'2023-05-06 05:39:46','2023-05-06 07:15:16'),(25,12,'hello2',0,0,0.00,0,'2023-05-06 05:40:05',NULL),(26,12,'test',0,0,0.00,0,'2023-05-06 08:35:52','2023-05-06 11:36:33'),(27,12,'New Dashboardhi',0,0,0.00,0,'2023-05-06 08:36:43','2023-05-06 08:38:35'),(28,12,'New Dashboard1',0,0,0.00,0,'2023-05-06 08:37:08','2023-05-06 08:38:05'),(29,12,'New Dashboard1',0,0,0.00,0,'2023-05-06 08:37:17','2023-05-06 08:38:05');
/*!40000 ALTER TABLE `dashboard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `listing`
--

DROP TABLE IF EXISTS `listing`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `listing` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dashboard_id` int NOT NULL,
  `catalogue_id` int NOT NULL,
  `sku` varchar(16) NOT NULL,
  `product_name` varchar(255) DEFAULT NULL,
  `product_description` varchar(1000) DEFAULT NULL,
  `brand` varchar(45) DEFAULT NULL,
  `category` varchar(45) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `sale_price` decimal(10,2) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `platform` varchar(45) DEFAULT NULL,
  `image` varchar(45) DEFAULT 'default_product.png',
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `dashboard_idx` (`dashboard_id`),
  KEY `listing_catalogue_idx` (`catalogue_id`),
  CONSTRAINT `catalogue_listing` FOREIGN KEY (`catalogue_id`) REFERENCES `catalogue` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `dashboard` FOREIGN KEY (`dashboard_id`) REFERENCES `dashboard` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='this product in a listing, for example product in my shop listing in amazon list of products with title mylist';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `listing`
--

LOCK TABLES `listing` WRITE;
/*!40000 ALTER TABLE `listing` DISABLE KEYS */;
INSERT INTO `listing` VALUES (20,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'amazon1','default_listing.png','2023-03-03 19:08:32','2023-05-09 02:11:18'),(21,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'amazon','default_listing.png','2023-03-03 21:45:45','2023-05-09 02:11:18'),(22,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'','default_listing.png','2023-03-04 00:50:06','2023-05-09 02:11:18'),(29,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'abc','default_listing.png','2023-03-06 03:11:06','2023-05-09 02:11:18'),(30,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'qwqw','default_listing.png','2023-03-06 03:12:08','2023-05-09 02:11:18'),(31,19,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'1','default_listing.png','2023-03-06 07:32:34','2023-05-09 02:11:18'),(33,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'amazon, ebay','default_listing.png','2023-03-08 20:05:06','2023-05-09 02:11:18'),(34,2,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'test','default_listing.png','2023-03-08 20:56:28','2023-05-09 02:11:18'),(35,2,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'test','default_listing.png','2023-03-08 20:59:54','2023-05-09 02:11:18'),(36,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'a','default_listing.png','2023-03-08 21:08:51','2023-05-09 02:11:18'),(37,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'a','default_listing.png','2023-03-08 21:09:56','2023-05-09 02:11:18'),(38,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'a','default_listing.png','2023-03-08 21:10:21','2023-05-09 02:11:18'),(39,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'a','default_listing.png','2023-03-08 21:11:07','2023-05-09 02:11:18'),(40,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'a','default_listing.png','2023-03-08 21:15:53','2023-05-09 02:11:18'),(41,3,1,'PRO1000','laptop','laptop it have brand : brashka and it\'s from catgory of electonric, the price of it is 388 but sale price is 358, sku: PRO1000','brashka','electonric',388.00,358.00,38,'test123','default_listing.png','2023-03-08 21:23:42','2023-05-09 02:11:18'),(42,3,17,'PRO1006','washmachine','washmachine it have brand : h&m and it\'s from catgory of electonric, the price of it is 600 but sale price is 500, sku: PRO1006','h&m','electonric',600.00,500.00,38,'aa','default_listing.png','2023-05-08 05:35:12','2023-05-09 02:11:18'),(43,5,15,'PRO1004','robot aram','robot aram it have brand : h&m and it\'s from catgory of electonric, the price of it is 10 but sale price is 8, sku: PRO1004','h&m','electonric',10.00,8.00,38,'','default_listing.png','2023-05-08 05:47:56','2023-05-09 02:11:18'),(44,3,62,'anudq1234','helloworld','hi','yes','newone',2.00,1.01,1,'yesits','default_listing.png','2023-05-09 02:18:49',NULL);
/*!40000 ALTER TABLE `listing` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order`
--

DROP TABLE IF EXISTS `order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_firstname` varchar(50) DEFAULT '',
  `customer_lastname` varchar(50) DEFAULT '',
  `listing_id` int NOT NULL,
  `quantity` int DEFAULT '0',
  `date` datetime DEFAULT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `listingpid_idx` (`listing_id`),
  CONSTRAINT `order_listing` FOREIGN KEY (`listing_id`) REFERENCES `listing` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order`
--

LOCK TABLES `order` WRITE;
/*!40000 ALTER TABLE `order` DISABLE KEYS */;
INSERT INTO `order` VALUES (1,'mr','test',20,1,'2023-03-04 07:50:00','2023-03-04 05:51:02','2023-05-08 06:16:19'),(5,'a','a',20,2,'2023-03-17 04:14:00','2023-03-06 02:14:23','2023-03-06 02:45:41'),(9,'test','test2',20,0,'2023-05-08 05:45:00','2023-05-08 02:45:27',NULL),(11,'teest','dqwdqwdq',20,0,'2023-05-09 05:54:00','2023-05-08 02:54:55',NULL),(16,'7mda1','yes',20,1,'2023-05-08 07:09:00','2023-05-08 04:09:39','2023-05-08 09:13:39'),(17,'new','newyues',42,1,'2023-05-08 08:36:00','2023-05-08 05:36:53',NULL),(18,'a','b',43,0,'2023-05-08 08:48:00','2023-05-08 05:48:15',NULL),(19,'t','t',21,1,'2023-05-23 10:44:00','2023-05-08 07:44:25',NULL),(20,'a','a',21,1,'2023-05-14 11:00:00','2023-05-08 08:00:56',NULL),(22,'a','a',21,1,'2023-05-08 02:42:00','2023-05-08 08:42:04',NULL),(23,'hi','a',21,1,'2023-05-08 02:42:00','2023-05-08 08:42:10','2023-05-08 09:13:10');
/*!40000 ALTER TABLE `order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase`
--

DROP TABLE IF EXISTS `purchase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase` (
  `id` int NOT NULL AUTO_INCREMENT,
  `supplier_id` int NOT NULL,
  `listing_id` int NOT NULL,
  `quantity` int DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `product_supplier_idx` (`supplier_id`),
  KEY `purchase_listing_idx` (`listing_id`),
  CONSTRAINT `product_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `supplier` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `purchase_listing` FOREIGN KEY (`listing_id`) REFERENCES `listing` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase`
--

LOCK TABLES `purchase` WRITE;
/*!40000 ALTER TABLE `purchase` DISABLE KEYS */;
INSERT INTO `purchase` VALUES (6,7,21,12,'2023-03-06 07:07:00','2023-03-05 01:07:12','2023-03-05 06:42:44'),(10,4,20,2,'2023-03-15 05:38:00','2023-03-05 03:38:37',NULL),(11,4,20,4,'2023-02-05 03:06:00','2023-03-05 04:11:49',NULL),(12,5,20,0,'2023-03-15 06:58:00','2023-03-05 04:58:45',NULL),(13,4,20,0,'2023-03-05 11:24:00','2023-03-05 06:30:12',NULL),(14,4,20,12,'2023-03-08 08:31:00','2023-03-05 06:31:07',NULL),(17,4,21,12,'2023-03-31 00:57:00','2023-03-05 06:57:57',NULL),(19,4,20,12,'2023-03-07 09:41:00','2023-03-06 07:41:10','2023-03-06 07:41:21'),(20,5,20,2,'2023-03-17 10:22:00','2023-03-06 08:22:36',NULL);
/*!40000 ALTER TABLE `purchase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role`
--

DROP TABLE IF EXISTS `role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role`
--

LOCK TABLES `role` WRITE;
/*!40000 ALTER TABLE `role` DISABLE KEYS */;
INSERT INTO `role` VALUES (1,'vendor','2023-02-26 23:06:44',NULL),(2,'admin','2023-02-26 23:06:44',NULL);
/*!40000 ALTER TABLE `role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `supplier`
--

DROP TABLE IF EXISTS `supplier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supplier` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `name` varchar(80) NOT NULL,
  `phone` varchar(45) NOT NULL,
  `address` varchar(125) NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_suppler_idx` (`user_id`),
  CONSTRAINT `user_suppler` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier`
--

LOCK TABLES `supplier` WRITE;
/*!40000 ALTER TABLE `supplier` DISABLE KEYS */;
INSERT INTO `supplier` VALUES (4,12,'test3','+201123312','hiqqwq','2023-03-04 21:48:36','2023-05-09 01:35:56'),(5,12,'Test12234','+12015550123','hi2','2023-03-04 21:50:07','2023-05-09 01:51:04'),(6,12,'test1','23','hi3','2023-03-04 21:52:37','2023-05-09 01:29:46'),(7,12,'test new','122','hi4','2023-03-04 23:03:31','2023-05-09 01:29:46'),(9,12,'safe 1','1221','hi5','2023-03-06 07:44:53','2023-05-09 01:29:46'),(10,12,'testnew','12345678','hinearest','2023-05-08 22:39:35',NULL),(11,12,'test','201555123','test','2023-05-08 23:20:43',NULL),(12,12,'dqdqwd','+12001230101','qdwdqwdwdqw','2023-05-09 00:33:40',NULL),(13,12,'dwqdwqd','201555464','ddqwqddqw','2023-05-09 00:34:19',NULL),(14,12,'qdwqdqd','01113722390','dqwqw','2023-05-09 00:35:28',NULL),(15,12,'qwddq','+201113722390','qddqwqdw','2023-05-09 00:36:27',NULL),(16,12,'dqwdwqdwqdw','+201113722390','qdwddwq','2023-05-09 00:37:08',NULL),(17,12,'qdwqdqdw','+201113722390','qdqdqwq','2023-05-09 00:38:33',NULL),(18,12,'dqwdqdqdqdq','01113722390','dqdqwddqw','2023-05-09 00:38:46',NULL),(19,12,'qdwdqwdqw','01113722390','dqwdwqdwq','2023-05-09 00:47:50',NULL),(20,12,'dqwdq','(kosomkyad)','qdwdqqwd','2023-05-09 00:49:01',NULL),(21,12,'dqwqdqwqdw','+201113722390','dqwdqwqd','2023-05-09 01:28:49',NULL);
/*!40000 ALTER TABLE `supplier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `uname` varchar(45) NOT NULL,
  `upass` varchar(500) NOT NULL,
  `email` varchar(255) NOT NULL,
  `image` varchar(100) DEFAULT 'default_profile.png',
  `created_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `approved` tinyint DEFAULT '1',
  `authenticated` tinyint DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uname_UNIQUE` (`uname`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (3,'zom6qn43','admin','$2b$12$CJjvgNCmLXxyHUyMU7VvZO9HpoY1AL.pncbDPcsUiqoXOZBDRJhdS','eyez3crn@gmail.com','default_user.png','2023-02-26 23:08:38','2023-02-27 02:10:25',1,0),(12,'lyfbrz42','3zlydgh1','$2b$12$mQBIsxp2KSOq687KY/EE.exy4eKtQDdjyCJWSkOhGoYDpHpgmgt8C','3zlydgh1@gmail.com','default_user.png','2023-02-27 03:57:07','2023-02-28 00:57:31',1,0),(13,'iu5znlim','idufbkhl','$2b$12$bxhaqRFBWFYTpy03N6yV8uRNRXkPFQ4J.V3C6OuScY.krM.9vXfCy','o3aij2ru@gmail.com','default_user.png','2023-02-27 03:59:02','2023-02-28 00:57:31',1,0),(15,'o2yhlqbz','aaj4ge1a','$2b$12$aji8XZQQxuOwDRBHgjpHge2m2elgx1a6EzzTlRKcZyb6RyPzmDwUm','zuq5lfch@gmail.com','default_user.png','2023-02-27 04:02:31','2023-02-28 00:57:31',1,0),(16,'x6d3fzfe','4zohe3nh','$2b$12$lWn1tIQyIGEggjROwvhdEOIrdi1JEfUehbtOTsW7lfHPlBXseTBB.','xyizkz2g@gmail.com','default_user.png','2023-02-27 04:05:41','2023-02-28 00:57:31',1,0),(17,'rniejh43','5e5ijdyh','$2b$12$iJdRW0tohROBSdxLOQZUQODOFr7vWE2NB8pX92PzLicJgreWPlGce','kzzgujrz@gmail.com','default_user.png','2023-02-27 04:07:14','2023-02-28 00:57:31',1,0),(19,'6i56mzha','x4rzzylu','$2b$12$fVXcgAxR4QGVZ1/qyn/rPeaLisbNmZhwmq4EYIB6IQZKBg2nMmK0W','di3x2m4h@gmail.com','default_user.png','2023-02-27 04:10:50','2023-02-28 00:57:31',1,0),(41,'6cuo53cf','u4ylo4lb','$2b$12$4iczvysM073NtTYOW4DTjudp56CBvqaNkZGECZKCAGiviJy03OeHe','zenulr41@gmail.com','default_user.png','2023-02-27 22:48:56','2023-02-28 00:57:31',1,0),(43,'umg4qyk2','yyxodzrb','$2b$12$GRCmeeNQTmeQhycggEBNTuG.zHv0z50CbomrSpMrd9MqsKMSPqpDy','giorlncu@gmail.com','default_user.png','2023-02-27 22:52:58','2023-02-28 00:57:31',1,0),(45,'test','new123','$2b$12$43bZGbc0/KIcBtVgYFSGieRRv6lSl7XfAZcBk99j53GsvhBM5RaKK','test@gmail.com','default_user.png','2023-03-06 07:28:40',NULL,1,0);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_roles`
--

DROP TABLE IF EXISTS `user_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `role_id` int DEFAULT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `role_idx` (`role_id`),
  KEY `user_idx` (`user_id`),
  CONSTRAINT `role` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_roles`
--

LOCK TABLES `user_roles` WRITE;
/*!40000 ALTER TABLE `user_roles` DISABLE KEYS */;
INSERT INTO `user_roles` VALUES (1,3,1,'2023-02-27 01:35:01','2023-02-27 01:35:19'),(2,3,2,'2023-02-27 01:38:43',NULL),(5,12,1,'2023-02-27 03:57:07',NULL),(6,13,1,'2023-02-27 03:59:02',NULL),(7,15,1,'2023-02-27 04:02:31',NULL),(8,16,1,'2023-02-27 04:05:41',NULL),(9,17,1,'2023-02-27 04:07:14',NULL),(11,19,1,'2023-02-27 04:10:50',NULL),(12,41,1,'2023-02-27 22:48:56',NULL),(13,43,1,'2023-02-27 22:52:58',NULL),(14,12,2,'2023-02-28 00:56:31',NULL),(15,45,1,'2023-03-06 07:28:40',NULL);
/*!40000 ALTER TABLE `user_roles` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-05-09 22:01:57
