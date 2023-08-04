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
  `sku` varchar(45) NOT NULL,
  `product_name` varchar(500) NOT NULL,
  `product_description` varchar(5000) DEFAULT 'no informations found for this product',
  `product_model` varchar(255) DEFAULT NULL,
  `brand` varchar(255) DEFAULT NULL,
  `category` varchar(255) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `sale_price` decimal(10,2) DEFAULT NULL,
  `quantity` varchar(255) DEFAULT NULL,
  `condition` varchar(255) DEFAULT NULL,
  `upc` varchar(255) DEFAULT NULL,
  `product_image` varchar(45) DEFAULT 'default_product.png',
  `user_id` int NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_product_idx` (`user_id`),
  CONSTRAINT `user_product` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2821 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `catalogue`
--

LOCK TABLES `catalogue` WRITE;
/*!40000 ALTER TABLE `catalogue` DISABLE KEYS */;
INSERT INTO `catalogue` VALUES (65,'test123','test','yes','yes','yes','yes',10.00,9.00,'1','true','theupc','default_product.png',47,'2023-05-17 07:22:44',NULL),(66,'test','product1','new product','model1','test','test',10.00,9.00,'6','TRUE','opc','default_product.png',48,'2023-06-11 07:44:53','2023-06-12 02:12:54'),(67,'test2','kitchen machine','kitchen machine description','model1','test','test',300.00,281.00,'2','true','opc','default_product.png',48,'2023-06-11 07:47:44','2023-06-12 02:12:54'),(71,'newone','yesits','new','yes','yes','yes',8.00,7.00,'2','a','notvalidated_quantity','default_product.png',48,'2023-06-12 02:08:22','2023-06-12 02:12:54'),(77,'abc12345','catalogue1','c','a','brand1','x',10.00,9.00,'1','c','b','default_product.png',49,'2023-06-16 00:50:53','2023-06-16 03:07:42'),(78,'deeeqw12','catalogue2','c','a','brand2','x',8.00,7.00,'4','c','b','default_product.png',49,'2023-06-16 00:51:14',NULL),(2816,'RUK-F11PRO','Ruko F11PRO GPS Drone with 4K Camera','6? ???? ?????? ????: F11PRO camera drone equipped with 2 powerful 11.1V 2500mAh intelligent batteries provides up to 60 minutes flight time in total, giving you more fun!\r\n???? ?? ????? ??? ??? ?? ???: It comes with beginner settings to let you get used to then you can use other functions further, easy to fly for all levels. Intelligent flight features like Follow Me Mode, Tap Fly, Point of Interest, Hand Gesture Shots make you fly like an expert to explore the fun of the aerial film, just One-click, It will fly itself and film your creative video.\r\n????? ? ???? ??????????: The brushless motor has stronger power, which can make the drone fly more stably and can resist the wind of level 6. The aluminum alloy casing is more durable than others of iron motors, it is durable for a long time used.\r\n?? ??? ??????: Experience splendid 4k Ultra HD picture quality and 2.9k video for stunning clarity, high contrast, and vivid colors. Bring amazing view sight. The camera with a ???°FOV lens and ??°adjustable camera gives a broad view of your memorable moment.\r\n??? ???? ?????? ???? ??????? ??? ??? ??????: The drone will auto-returning to the takeoff location when it\'s lost signal, or low power, don\'t have to worry about losing your drone, just enjoy the fun of flying.','F11PRO','Ruko','Drones',499.25,419.99,'4','Brand New','666000002927','default_product.png',12,'2023-07-31 00:50:20','2023-08-04 09:14:49'),(2817,'TRI-1120-XGO','Tribit XSound Go Bluetooth Speaker - 12W Portable Loud Stereo - Open Box','Smaller Size, Bigger Sound\nDon’t let its compact size fool you— the Tribit XSound Go provides sound that’s larger than life. Dual 6W high-performance drivers and a premium passive bass radiator create soaring highs, electrifying mids, and rich bass. Your music will be smooth and clear, even when cranked to maximum volume!\n\nIncredible 24 Hour Playtime\nNo outlet? No problem. A powerful, rechargeable lithium ion battery offers up to 24 hours of non-stop use. It’s the perfect speaker for traveling, camping trips, barbecues, or anywhere else you might need a little ambience.\n\nTake Your Tunes on the Road\nAt only 13oz, this featherlight portable speaker is easy to carry from place to place. Throw it in your backpack, purse, or beach bag for music on the go. We’ve also attached a convenient carrying strap for maximum portability.\n\nPool Party Waterproof\nWith top of the line IPX7 waterproofing, water won’t slow you down. It’s perfect for the pool, the shower, the backyard, and everywhere in between.\n\nWireless Bluetooth Connection\nAdvanced bluetooth 4.2 technology provides a completely wireless connection with an amazing 66ft range! Pairing is simple— Just enter your device’s bluetooth settings, click on “Tribit XSound Go”, and enjoy.\n\nUniversal Compatibility\nThe Tribit XSound Go is compatible with all bluetooth enabled devices. Pair it with your iPhone, Samsung, Amazon Echo/ Echo Dot, laptop and so much more. A 3.5 mm audio cable (not included) can be used to play audio from desktop computers, TVs, MP3 players.','BTS20','Tribit','Portable, Wireless & Compact Speaker Systems',39.99,39.99,'12','Open Box','6971136362765','default_product.png',12,'2023-07-31 00:50:21',NULL),(2819,'TRI-1120-XGO','Tribit XSound Go Bluetooth Speaker - 12W Portable Loud Stereo - Open Box','Smaller Size, Bigger Sound\r\nDon’t let its compact size fool you— the Tribit XSound Go provides sound that’s larger than life. Dual 6W high-performance drivers and a premium passive bass radiator create soaring highs, electrifying mids, and rich bass. Your music will be smooth and clear, even when cranked to maximum volume!\r\n\r\nIncredible 24 Hour Playtime\r\nNo outlet? No problem. A powerful, rechargeable lithium ion battery offers up to 24 hours of non-stop use. It’s the perfect speaker for traveling, camping trips, barbecues, or anywhere else you might need a little ambience.\r\n\r\nTake Your Tunes on the Road\r\nAt only 13oz, this featherlight portable speaker is easy to carry from place to place. Throw it in your backpack, purse, or beach bag for music on the go. We’ve also attached a convenient carrying strap for maximum portability.\r\n\r\nPool Party Waterproof\r\nWith top of the line IPX7 waterproofing, water won’t slow you down. It’s perfect for the pool, the shower, the backyard, and everywhere in between.\r\n\r\nWireless Bluetooth Connection\r\nAdvanced bluetooth 4.2 technology provides a completely wireless connection with an amazing 66ft range! Pairing is simple— Just enter your device’s bluetooth settings, click on “Tribit XSound Go”, and enjoy.\r\n\r\nUniversal Compatibility\r\nThe Tribit XSound Go is compatible with all bluetooth enabled devices. Pair it with your iPhone, Samsung, Amazon Echo/ Echo Dot, laptop and so much more. A 3.5 mm audio cable (not included) can be used to play audio from desktop computers, TVs, MP3 players.','BTS20','Tribit','Portable, Wireless & Compact Speaker Systems',39.99,39.99,'10','Open Box','6971136362765','default_product.png',52,'2023-07-31 01:02:51','2023-08-03 18:39:36'),(2820,'RUK-F11PRO','Ruko F11PRO GPS Drone with 4K Camera','6? ???? ?????? ????: F11PRO camera drone equipped with 2 powerful 11.1V 2500mAh intelligent batteries provides up to 60 minutes flight time in total, giving you more fun!\n???? ?? ????? ??? ??? ?? ???: It comes with beginner settings to let you get used to then you can use other functions further, easy to fly for all levels. Intelligent flight features like Follow Me Mode, Tap Fly, Point of Interest, Hand Gesture Shots make you fly like an expert to explore the fun of the aerial film, just One-click, It will fly itself and film your creative video.\n????? ? ???? ??????????: The brushless motor has stronger power, which can make the drone fly more stably and can resist the wind of level 6. The aluminum alloy casing is more durable than others of iron motors, it is durable for a long time used.\n?? ??? ??????: Experience splendid 4k Ultra HD picture quality and 2.9k video for stunning clarity, high contrast, and vivid colors. Bring amazing view sight. The camera with a ???°FOV lens and ??°adjustable camera gives a broad view of your memorable moment.\n??? ???? ?????? ???? ??????? ??? ??? ??????: The drone will auto-returning to the takeoff location when it\'s lost signal, or low power, don\'t have to worry about losing your drone, just enjoy the fun of flying.','F11PRO','Ruko','Drones',499.25,419.99,'1','Brand New','666000002927','default_product.png',52,'2023-07-31 20:39:16','2023-08-01 02:54:34');
/*!40000 ALTER TABLE `catalogue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `catalogue_locations`
--

DROP TABLE IF EXISTS `catalogue_locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `catalogue_locations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `catalogue_id` int NOT NULL,
  `location_id` int NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `selected_catalogue_idx` (`catalogue_id`),
  KEY `selecte_warehouse_location_idx` (`location_id`),
  CONSTRAINT `selecte_warehouse_location` FOREIGN KEY (`location_id`) REFERENCES `warehouse_locations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `selected_catalogue` FOREIGN KEY (`catalogue_id`) REFERENCES `catalogue` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2127 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `catalogue_locations`
--

LOCK TABLES `catalogue_locations` WRITE;
/*!40000 ALTER TABLE `catalogue_locations` DISABLE KEYS */;
INSERT INTO `catalogue_locations` VALUES (2115,2816,23,'2023-07-31 00:50:20',NULL),(2116,2816,17,'2023-07-31 00:50:20',NULL),(2117,2816,18,'2023-07-31 00:50:20',NULL),(2118,2817,24,'2023-07-31 00:50:21',NULL),(2122,2819,28,'2023-07-31 01:02:51',NULL),(2123,2820,25,'2023-07-31 20:39:16',NULL),(2124,2820,26,'2023-07-31 20:39:16',NULL),(2125,2820,27,'2023-07-31 20:39:16',NULL),(2126,2819,25,'2023-08-03 18:39:36',NULL);
/*!40000 ALTER TABLE `catalogue_locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `catalogue_locations_bins`
--

DROP TABLE IF EXISTS `catalogue_locations_bins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `catalogue_locations_bins` (
  `id` int NOT NULL AUTO_INCREMENT,
  `location_id` int DEFAULT NULL,
  `bin_id` int DEFAULT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `qdwqdqqd_idx` (`location_id`),
  KEY `qd_idx` (`bin_id`),
  CONSTRAINT `parent_catalogue_location` FOREIGN KEY (`location_id`) REFERENCES `catalogue_locations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `parent_location_bin` FOREIGN KEY (`bin_id`) REFERENCES `location_bins` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1935 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `catalogue_locations_bins`
--

LOCK TABLES `catalogue_locations_bins` WRITE;
/*!40000 ALTER TABLE `catalogue_locations_bins` DISABLE KEYS */;
INSERT INTO `catalogue_locations_bins` VALUES (1934,2126,15,'2023-08-03 18:39:37',NULL);
/*!40000 ALTER TABLE `catalogue_locations_bins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dashboard`
--

DROP TABLE IF EXISTS `dashboard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dashboard` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(45) DEFAULT 'New Dashboard',
  `num_of_listings` int DEFAULT '0',
  `num_of_orders` int DEFAULT '0',
  `sum_of_monthly_purchases` decimal(12,2) DEFAULT '0.00',
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dashboard`
--

LOCK TABLES `dashboard` WRITE;
/*!40000 ALTER TABLE `dashboard` DISABLE KEYS */;
INSERT INTO `dashboard` VALUES (3,'Dashboard',1,9,NULL,'2023-02-28 04:58:06','2023-08-04 09:14:49'),(31,'Dashboard',0,0,0.00,'2023-05-17 07:15:14',NULL),(32,'Dashboard',3,2,1210.00,'2023-06-11 07:42:37','2023-06-11 22:37:57'),(33,'Dashboard',1,1,NULL,'2023-06-16 00:49:35','2023-06-16 03:07:42'),(34,'Dashboard',0,0,0.00,'2023-07-26 04:28:36',NULL),(35,'Dashboard',0,0,0.00,'2023-07-30 23:02:04',NULL),(36,'Dashboard',2,3,499.25,'2023-07-31 01:02:34','2023-08-01 04:43:26');
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
  `sku` varchar(45) DEFAULT NULL,
  `product_name` varchar(500) DEFAULT NULL,
  `product_description` varchar(5000) DEFAULT NULL,
  `brand` varchar(255) DEFAULT NULL,
  `category` varchar(255) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `sale_price` decimal(10,2) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `image` varchar(45) DEFAULT 'default_product.png',
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `dashboard_idx` (`dashboard_id`),
  KEY `listing_catalogue_idx` (`catalogue_id`),
  KEY `sku_index` (`sku`),
  CONSTRAINT `catalogue_listing` FOREIGN KEY (`catalogue_id`) REFERENCES `catalogue` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `dashboard` FOREIGN KEY (`dashboard_id`) REFERENCES `dashboard` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=163 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='this product in a listing, for example product in my shop listing in amazon list of products with title mylist';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `listing`
--

LOCK TABLES `listing` WRITE;
/*!40000 ALTER TABLE `listing` DISABLE KEYS */;
INSERT INTO `listing` VALUES (46,31,65,'qwxwq','robot aram1','','xwq','wq',10.00,20.00,12,'default_listing.png','2023-05-17 07:22:56','2023-06-01 20:56:36'),(57,32,66,'test','product1','new product','test','test',10.00,9.00,6,'default_listing.png','2023-06-11 09:00:40','2023-06-12 02:12:54'),(58,32,67,'test2','kitchen machine','kitchen machine description','test','test',300.00,281.00,2,'default_listing.png','2023-06-11 12:38:53','2023-06-12 02:12:54'),(62,32,66,'test','product1','new product','test','test',10.00,9.00,6,'default_listing.png','2023-06-11 22:37:57','2023-06-12 02:12:54'),(70,33,77,'abc12345','catalogue1','c','brand1','x',10.00,9.00,1,'default_listing.png','2023-06-16 02:28:39','2023-06-16 03:07:42'),(158,3,2816,'RUK-F11PRO','Ruko F11PRO GPS Drone with 4K Camera','6? ???? ?????? ????: F11PRO camera drone equipped with 2 powerful 11.1V 2500mAh intelligent batteries provides up to 60 minutes flight time in total, giving you more fun!\r\n???? ?? ????? ??? ??? ?? ???: It comes with beginner settings to let you get used to then you can use other functions further, easy to fly for all levels. Intelligent flight features like Follow Me Mode, Tap Fly, Point of Interest, Hand Gesture Shots make you fly like an expert to explore the fun of the aerial film, just One-click, It will fly itself and film your creative video.\r\n????? ? ???? ??????????: The brushless motor has stronger power, which can make the drone fly more stably and can resist the wind of level 6. The aluminum alloy casing is more durable than others of iron motors, it is durable for a long time used.\r\n?? ??? ??????: Experience splendid 4k Ultra HD picture quality and 2.9k video for stunning clarity, high contrast, and vivid colors. Bring amazing view sight. The camera with a ???°FOV lens and ??°adjustable camera gives a broad view of your memorable moment.\r\n??? ???? ?????? ???? ??????? ??? ??? ??????: The drone will auto-returning to the takeoff location when it\'s lost signal, or low power, don\'t have to worry about losing your drone, just enjoy the fun of flying.','Ruko','Drones',499.25,419.99,4,'default_listing.png','2023-07-31 00:55:57','2023-08-04 09:14:49'),(161,36,2820,'RUK-F11PRO','Ruko F11PRO GPS Drone with 4K Camera','6? ???? ?????? ????: F11PRO camera drone equipped with 2 powerful 11.1V 2500mAh intelligent batteries provides up to 60 minutes flight time in total, giving you more fun!\n???? ?? ????? ??? ??? ?? ???: It comes with beginner settings to let you get used to then you can use other functions further, easy to fly for all levels. Intelligent flight features like Follow Me Mode, Tap Fly, Point of Interest, Hand Gesture Shots make you fly like an expert to explore the fun of the aerial film, just One-click, It will fly itself and film your creative video.\n????? ? ???? ??????????: The brushless motor has stronger power, which can make the drone fly more stably and can resist the wind of level 6. The aluminum alloy casing is more durable than others of iron motors, it is durable for a long time used.\n?? ??? ??????: Experience splendid 4k Ultra HD picture quality and 2.9k video for stunning clarity, high contrast, and vivid colors. Bring amazing view sight. The camera with a ???°FOV lens and ??°adjustable camera gives a broad view of your memorable moment.\n??? ???? ?????? ???? ??????? ??? ??? ??????: The drone will auto-returning to the takeoff location when it\'s lost signal, or low power, don\'t have to worry about losing your drone, just enjoy the fun of flying.','Ruko','Drones',499.25,419.99,1,'default_listing.png','2023-07-31 22:52:36','2023-08-01 02:54:34'),(162,36,2819,'TRI-1120-XGO','Tribit XSound Go Bluetooth Speaker - 12W Portable Loud Stereo - Open Box','Smaller Size, Bigger Sound\r\nDon’t let its compact size fool you— the Tribit XSound Go provides sound that’s larger than life. Dual 6W high-performance drivers and a premium passive bass radiator create soaring highs, electrifying mids, and rich bass. Your music will be smooth and clear, even when cranked to maximum volume!\r\n\r\nIncredible 24 Hour Playtime\r\nNo outlet? No problem. A powerful, rechargeable lithium ion battery offers up to 24 hours of non-stop use. It’s the perfect speaker for traveling, camping trips, barbecues, or anywhere else you might need a little ambience.\r\n\r\nTake Your Tunes on the Road\r\nAt only 13oz, this featherlight portable speaker is easy to carry from place to place. Throw it in your backpack, purse, or beach bag for music on the go. We’ve also attached a convenient carrying strap for maximum portability.\r\n\r\nPool Party Waterproof\r\nWith top of the line IPX7 waterproofing, water won’t slow you down. It’s perfect for the pool, the shower, the backyard, and everywhere in between.\r\n\r\nWireless Bluetooth Connection\r\nAdvanced bluetooth 4.2 technology provides a completely wireless connection with an amazing 66ft range! Pairing is simple— Just enter your device’s bluetooth settings, click on “Tribit XSound Go”, and enjoy.\r\n\r\nUniversal Compatibility\r\nThe Tribit XSound Go is compatible with all bluetooth enabled devices. Pair it with your iPhone, Samsung, Amazon Echo/ Echo Dot, laptop and so much more. A 3.5 mm audio cable (not included) can be used to play audio from desktop computers, TVs, MP3 players.','Tribit','Portable, Wireless & Compact Speaker Systems',39.99,39.99,10,'default_listing.png','2023-08-01 00:26:51','2023-08-03 18:39:36');
/*!40000 ALTER TABLE `listing` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `listing_platform`
--

DROP TABLE IF EXISTS `listing_platform`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `listing_platform` (
  `id` int NOT NULL AUTO_INCREMENT,
  `listing_id` int NOT NULL,
  `platform_id` int NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `listing_platform_idx` (`listing_id`),
  KEY `selected_plateform_idx` (`platform_id`),
  CONSTRAINT `listing_platform` FOREIGN KEY (`listing_id`) REFERENCES `listing` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `selected_plateform` FOREIGN KEY (`platform_id`) REFERENCES `platform` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `listing_platform`
--

LOCK TABLES `listing_platform` WRITE;
/*!40000 ALTER TABLE `listing_platform` DISABLE KEYS */;
INSERT INTO `listing_platform` VALUES (31,62,2,'2023-06-11 22:46:06',NULL),(33,62,11,'2023-06-12 01:10:58',NULL),(43,70,14,'2023-06-16 02:28:39',NULL),(66,161,32,'2023-08-01 00:27:34',NULL),(67,161,33,'2023-08-01 04:15:39',NULL),(68,162,33,'2023-08-03 20:01:46',NULL);
/*!40000 ALTER TABLE `listing_platform` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `location_bins`
--

DROP TABLE IF EXISTS `location_bins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `location_bins` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `location_id` int NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `warehouse_location_bins_idx` (`location_id`),
  CONSTRAINT `warehouse_location_bins` FOREIGN KEY (`location_id`) REFERENCES `warehouse_locations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `location_bins`
--

LOCK TABLES `location_bins` WRITE;
/*!40000 ALTER TABLE `location_bins` DISABLE KEYS */;
INSERT INTO `location_bins` VALUES (1,'y2',3,'2023-07-09 11:23:21','2023-07-17 15:50:12'),(2,'y',3,'2023-07-09 11:25:07',NULL),(6,'hi',6,'2023-07-09 12:59:21',NULL),(8,'new',7,'2023-07-09 23:10:13',NULL),(9,'new2',7,'2023-07-09 23:10:21',NULL),(10,'new4',7,'2023-07-09 23:10:28',NULL),(11,'bin_1',8,'2023-07-26 04:27:28',NULL),(12,'bin_x',9,'2023-07-26 04:29:11',NULL),(14,'test',3,'2023-07-30 23:16:32',NULL),(15,'a',25,'2023-07-31 01:14:22',NULL);
/*!40000 ALTER TABLE `location_bins` ENABLE KEYS */;
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
  `tax` decimal(10,2) DEFAULT '0.00',
  `shipping` decimal(10,2) DEFAULT '0.00',
  `shipping_tax` decimal(10,2) DEFAULT '0.00',
  `commission` decimal(10,2) DEFAULT '0.00',
  `total_cost` decimal(10,2) DEFAULT '0.00',
  PRIMARY KEY (`id`),
  KEY `listingpid_idx` (`listing_id`),
  CONSTRAINT `order_listing` FOREIGN KEY (`listing_id`) REFERENCES `listing` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=110 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order`
--

LOCK TABLES `order` WRITE;
/*!40000 ALTER TABLE `order` DISABLE KEYS */;
INSERT INTO `order` VALUES (63,'a','a',57,1,'2023-06-11 15:34:00','2023-06-11 12:34:33','2023-06-11 12:36:07',0.00,0.00,0.00,0.00,0.00),(65,'a','b',58,2,'2023-06-11 15:39:00','2023-06-11 12:39:24',NULL,0.00,0.00,0.00,0.00,0.00),(75,'a','b',70,1,'2023-06-16 06:07:00','2023-06-16 03:07:42',NULL,0.00,0.00,0.00,0.00,0.00),(89,'new','order',161,1,'2023-08-01 05:46:00','2023-08-01 02:46:10',NULL,0.00,0.00,0.00,0.00,0.00),(91,'a','b',162,2,'2023-08-01 07:43:00','2023-08-01 04:43:25',NULL,0.00,0.00,0.00,0.00,0.00),(92,'a','b',158,1,'2023-08-04 00:22:00','2023-08-03 21:22:49',NULL,0.00,0.00,0.00,0.00,0.00),(102,'test','test',158,1,'2023-08-04 11:03:00','2023-08-04 08:35:36',NULL,0.00,0.00,0.00,0.00,0.00),(103,'test','test',158,1,'2023-08-04 11:03:00','2023-08-04 08:37:10',NULL,0.00,0.00,0.00,0.00,0.00),(104,'test','test',158,1,'2023-08-04 11:03:00','2023-08-04 08:37:36',NULL,0.00,0.00,0.00,0.00,0.00),(105,'test','test',158,1,'2023-08-04 11:03:00','2023-08-04 08:43:38',NULL,0.00,0.00,0.00,0.00,500.25),(106,'test','test',158,1,'2023-08-04 11:03:00','2023-08-04 09:02:27',NULL,0.00,2.00,0.00,0.00,501.25),(107,'test','test',158,1,'2023-08-04 11:03:00','2023-08-04 09:03:34',NULL,0.00,0.00,0.00,0.00,499.25),(108,'test','test',158,1,'2023-08-04 11:03:00','2023-08-04 09:07:10',NULL,0.00,0.00,0.00,0.00,499.25),(109,'a','b',158,1,'2023-08-04 12:14:00','2023-08-04 09:14:49','2023-08-04 09:45:18',3.00,1.00,0.00,2.00,505.25);
/*!40000 ALTER TABLE `order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `platform`
--

DROP TABLE IF EXISTS `platform`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `dashboard_id` int NOT NULL,
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `plateform_dashboard_idx` (`dashboard_id`),
  CONSTRAINT `dashboard_platform` FOREIGN KEY (`dashboard_id`) REFERENCES `dashboard` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `platform`
--

LOCK TABLES `platform` WRITE;
/*!40000 ALTER TABLE `platform` DISABLE KEYS */;
INSERT INTO `platform` VALUES (2,'ebay',32,'2023-06-11 21:13:34','2023-06-11 21:36:53'),(11,'amazon',32,'2023-06-12 01:10:49',NULL),(14,'ebay',33,'2023-06-16 00:51:36',NULL),(15,'amazon',33,'2023-06-16 00:51:42',NULL),(30,'amazon',3,'2023-07-30 23:24:10',NULL),(31,'ebay',3,'2023-07-30 23:24:14',NULL),(32,'ebay',36,'2023-08-01 00:27:20',NULL),(33,'amazon',36,'2023-08-01 00:27:26',NULL);
/*!40000 ALTER TABLE `platform` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=152 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase`
--

LOCK TABLES `purchase` WRITE;
/*!40000 ALTER TABLE `purchase` DISABLE KEYS */;
INSERT INTO `purchase` VALUES (123,23,57,1,'2023-06-11 15:33:00','2023-06-11 12:33:17','2023-06-11 12:34:00'),(124,23,58,2,'2023-06-11 15:39:00','2023-06-11 12:39:07',NULL),(125,23,58,2,'2023-06-11 15:39:00','2023-06-11 12:39:39',NULL),(151,27,161,1,'2023-08-01 05:54:00','2023-08-01 02:54:34',NULL);
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
  `test` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_suppler_idx` (`user_id`),
  CONSTRAINT `user_suppler` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier`
--

LOCK TABLES `supplier` WRITE;
/*!40000 ALTER TABLE `supplier` DISABLE KEYS */;
INSERT INTO `supplier` VALUES (4,12,'test3','+201123312','hiqqwq','2023-03-04 21:48:36','2023-05-09 01:35:56',NULL),(5,12,'Test12234','+12015550123','hi2','2023-03-04 21:50:07','2023-05-09 01:51:04',NULL),(6,12,'test1','23','hi3','2023-03-04 21:52:37','2023-05-09 01:29:46',NULL),(7,12,'test new','122','hi4','2023-03-04 23:03:31','2023-05-09 01:29:46',NULL),(9,12,'safe 1','1221','hi5','2023-03-06 07:44:53','2023-05-09 01:29:46',NULL),(10,12,'testnew','12345678','hinearest','2023-05-08 22:39:35',NULL,NULL),(11,12,'test','201555123','test','2023-05-08 23:20:43',NULL,NULL),(12,12,'dqdqwd','+12001230101','qdwdqwdwdqw','2023-05-09 00:33:40',NULL,NULL),(13,12,'dwqdwqd','201555464','ddqwqddqw','2023-05-09 00:34:19',NULL,NULL),(20,12,'dqwdq','','qdwdqqwd','2023-05-09 00:49:01','2023-05-15 16:41:06',NULL),(23,48,'supplier1','+12015550123','new address','2023-06-11 07:46:20',NULL,NULL),(24,48,'supplier2','+12015550124','another address','2023-06-11 07:46:43',NULL,NULL),(25,49,'t','+12015551234','t','2023-06-16 00:52:39',NULL,NULL),(26,12,'trusted supplier','+12015550123','nourth america','2023-07-03 17:50:22',NULL,NULL),(27,52,'test','+12015550124','new address','2023-08-01 02:52:22',NULL,NULL);
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
  `dashboard_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uname_UNIQUE` (`uname`),
  UNIQUE KEY `email_UNIQUE` (`email`),
  UNIQUE KEY `dashboard_id_UNIQUE` (`dashboard_id`),
  CONSTRAINT `parent_dashboard` FOREIGN KEY (`dashboard_id`) REFERENCES `dashboard` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (12,'lyfbrz42','3zlydgh1','$2b$12$mQBIsxp2KSOq687KY/EE.exy4eKtQDdjyCJWSkOhGoYDpHpgmgt8C','3zlydgh1@gmail.com','default_user.png','2023-02-27 03:57:07','2023-02-28 00:57:31',1,0,3),(47,'test','test123','$2b$12$E5.42Q6uydNgJArWCQsLgelB1k.V6E.ujbIv2RW2PjTuikth23Ni6','test12323@gmail.com','default_user.png','2023-05-17 07:15:14',NULL,1,0,31),(48,'admin','admin123','$2b$12$N8RPCNRa2amNaDlEtDN8keDP4HA/UiXys35RvBJU4xnPGqBV3z9P.','testmail@gmail.com','default_user.png','2023-06-11 07:42:38',NULL,1,0,32),(49,'newuser','user1','$2b$12$AJRpHtcNA9dRxXAG9BEr2.Tf3YoQNwa0HBSnpYn6gRXBXv//6FbiS','noob@gmail.com','default_user.png','2023-06-16 00:49:36',NULL,1,0,33),(50,'test','123456812','$2b$12$n7EQ9tsabjC.K.YsQEnFO.Pn9k2nHCtxuyyg1lULs1U7jmx4wzVD.','test@gmail.com','default_user.png','2023-07-26 04:28:37',NULL,1,0,34),(51,'a','a12345678','$2b$12$ZDZvXHSt3sAK/BTguEtXAuYbiB5KAFA9F4hWPVhxCwL/luQ208sGW','a12345678@gmail.com','default_user.png','2023-07-30 23:02:04','2023-07-30 23:07:30',1,0,35),(52,'qcqwcq','cqcq123455','$2b$12$piqeGZ7HKUuykvQXKVp3IuI2M/QnYlItPhNpopSGxd9j7Vt6.ZyU2','cqcq123455@gmail.com','default_user.png','2023-07-31 01:02:35',NULL,1,0,36);
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
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_roles`
--

LOCK TABLES `user_roles` WRITE;
/*!40000 ALTER TABLE `user_roles` DISABLE KEYS */;
INSERT INTO `user_roles` VALUES (5,12,1,'2023-02-27 03:57:07',NULL),(14,12,2,'2023-02-28 00:56:31',NULL),(17,47,1,'2023-05-17 07:15:14',NULL),(18,48,1,'2023-06-11 07:42:39',NULL),(19,48,2,'2023-06-11 07:43:25','2023-06-11 07:43:46'),(20,49,1,'2023-06-16 00:49:36',NULL),(21,50,1,'2023-07-26 04:28:37',NULL),(22,51,1,'2023-07-30 23:02:04',NULL),(23,52,1,'2023-07-31 01:02:35',NULL);
/*!40000 ALTER TABLE `user_roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `warehouse_locations`
--

DROP TABLE IF EXISTS `warehouse_locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `warehouse_locations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `dashboard_id` int NOT NULL,
  `default` tinyint DEFAULT '0',
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `dashboard_locations_idx` (`dashboard_id`),
  CONSTRAINT `dashboard_locations` FOREIGN KEY (`dashboard_id`) REFERENCES `dashboard` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `warehouse_locations`
--

LOCK TABLES `warehouse_locations` WRITE;
/*!40000 ALTER TABLE `warehouse_locations` DISABLE KEYS */;
INSERT INTO `warehouse_locations` VALUES (3,'test',3,0,'2023-07-09 09:45:38',NULL),(6,'test',32,0,'2023-07-09 12:59:17',NULL),(7,'t',3,0,'2023-07-09 22:23:54',NULL),(8,'hello_world',3,0,'2023-07-26 04:27:14',NULL),(9,'hello_only',34,0,'2023-07-26 04:28:59',NULL),(17,' new',3,0,'2023-07-27 22:32:40',NULL),(18,' yes',3,0,'2023-07-27 22:32:40',NULL),(20,'Warehouse',3,0,'2023-07-29 06:33:30',NULL),(21,'Out of stock',3,0,'2023-07-29 06:33:37',NULL),(22,'',3,0,'2023-07-29 06:33:37',NULL),(23,'location_namex',3,0,'2023-07-31 00:50:20',NULL),(24,'noob_location',3,0,'2023-07-31 00:50:21',NULL),(25,'location_namex',36,0,'2023-07-31 01:02:50',NULL),(26,' new',36,0,'2023-07-31 01:02:50',NULL),(27,' yes',36,0,'2023-07-31 01:02:51',NULL),(28,'noob_location',36,0,'2023-07-31 01:02:51',NULL);
/*!40000 ALTER TABLE `warehouse_locations` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-08-04 13:58:02
