CREATE TABLE "location" (
  "departure station" TEXT,
  "location capitalized" TEXT,
  "guest house name" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "location part" TEXT,
  "str" TEXT,
  "address" INTEGER,
  "location (restaurant:5)" TEXT,
  "location abbrev" TEXT,
  "location area" TEXT,
  "location str" TEXT,
  "restaurant name" TEXT,
  "venue name" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("address")
);

CREATE TABLE "time" (
  "time id" INTEGER,
  "day of week str" TEXT,
  "departure time" INTEGER,
  "time" TIME,
  "time int" TIME,
  "time str" INTEGER,
  "train id" TIME,
  "date" TEXT,
  "day of week" TEXT,
  "train id (hotel:23)" INTEGER,
  "date (restaurant:3)" TEXT,
  "day of week (restaurant:4)" TEXT,
  "reservation time" INTERVAL,
  "time int (restaurant:19)" TIME,
  PRIMARY KEY ("time id")
);

CREATE TABLE "price" (
  "price key" INTEGER,
  "currency" NUMERIC(10, 2),
  "price" NUMERIC(10, 2),
  "total fee" TEXT,
  "price range" TEXT,
  "price range str" TEXT,
  "price (restaurant:12)" TEXT,
  "price range (restaurant:13)" TEXT,
  "price range str (restaurant:14)" TEXT,
  "str" TEXT,
  PRIMARY KEY ("price key")
);

CREATE TABLE "reference_number" (
  "id" INTEGER,
  "reference number" INTEGER,
  "reference number (restaurant:15)" INTEGER,
  PRIMARY KEY ("id")
);
