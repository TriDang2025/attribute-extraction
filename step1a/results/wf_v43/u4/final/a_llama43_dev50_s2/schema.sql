CREATE TABLE "hotel" (
  "hotel name key" INTEGER,
  "hotel name" TEXT,
  PRIMARY KEY ("hotel name key")
);

CREATE TABLE "restaurant" (
  "restaurant name key" INTEGER,
  "restaurant name" TEXT,
  PRIMARY KEY ("restaurant name key")
);

CREATE TABLE "reference" (
  "reference number key" INTEGER,
  "reference number" INTEGER,
  "train id" INTEGER,
  "reference number (hotel:13)" INTEGER,
  "reference number (restaurant:17)" INTEGER,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "reservation" (
  "id" INTEGER,
  "table" TEXT,
  "reservation time" INTERVAL,
  "reference id" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("reference id") REFERENCES "reference" ("reference number key")
);

CREATE TABLE "location" (
  "location key" INTEGER,
  "departure location" TEXT,
  "destination" TEXT,
  "location capitalized" TEXT,
  "location str" TEXT,
  "departure station" TEXT,
  "location" TEXT,
  "location adverb" TEXT,
  "location snake" TEXT,
  "location str (restaurant:9)" TEXT,
  "restaurant address" TEXT,
  "address" TEXT,
  "location (restaurant:8)" TEXT,
  "pickup location" TEXT,
  "hotel id" INTEGER,
  PRIMARY KEY ("location key"),
  FOREIGN KEY ("hotel id") REFERENCES "hotel" ("hotel name key")
);

CREATE TABLE "time" (
  "time" INTEGER,
  "departure time" TIME,
  "day of week relative" TEXT,
  "day of week" TEXT,
  "time minutes" INTERVAL,
  "start date" TEXT,
  "time int" TIME,
  "time str" TEXT,
  PRIMARY KEY ("time")
);

CREATE TABLE "price" (
  "price key" INTEGER,
  "total fee" NUMERIC(10, 2),
  "price str" TEXT,
  "price range" TEXT,
  "stars" INTEGER,
  "moderate price range" TEXT,
  "cuisine" TEXT,
  "expensive" TEXT,
  "phone number" INTEGER,
  "price range (restaurant:15)" TEXT,
  "cheap" TEXT,
  "price" TEXT,
  PRIMARY KEY ("price key")
);

CREATE TABLE "hotel_reference" (
  "hotel_reference id" INTEGER,
  "hotel id" INTEGER,
  "reference id" INTEGER,
  PRIMARY KEY ("hotel_reference id"),
  FOREIGN KEY ("hotel id") REFERENCES "hotel" ("hotel name key"),
  FOREIGN KEY ("reference id") REFERENCES "reference" ("reference number key")
);

CREATE TABLE "restaurant_reference" (
  "restaurant_reference id" INTEGER,
  "restaurant id" INTEGER,
  "reference id" INTEGER,
  PRIMARY KEY ("restaurant_reference id"),
  FOREIGN KEY ("restaurant id") REFERENCES "restaurant" ("restaurant name key"),
  FOREIGN KEY ("reference id") REFERENCES "reference" ("reference number key")
);
