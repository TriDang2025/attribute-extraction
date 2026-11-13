CREATE TABLE "train_reference" (
  "reference number key" INTEGER,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "train_price" (
  "id" INTEGER,
  "total fee" NUMERIC(10, 2),
  "price str" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "train_destination" (
  "day of week key" INTEGER,
  "day of week" TEXT,
  "day of week relative" TEXT,
  PRIMARY KEY ("day of week key")
);

CREATE TABLE "train_departure_time" (
  "id" INTEGER,
  "time minutes" INTERVAL,
  "departure time" TIME,
  "time int" TIME,
  "time str" TEXT,
  "reservation time" INTERVAL,
  "train_reference id" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("train_reference id") REFERENCES "train_reference" ("reference number key")
);

CREATE TABLE "train_departure_location" (
  "departure location key" INTEGER,
  "departure location" TEXT,
  "departure station" TEXT,
  PRIMARY KEY ("departure location key")
);

CREATE TABLE "train_location" (
  "location" INTEGER,
  "destination" TEXT,
  "location str" TEXT,
  "location capitalized" TEXT,
  PRIMARY KEY ("location")
);

CREATE TABLE "hotel_id_reference_number" (
  "reference number key" INTEGER,
  "hotel name" TEXT,
  "location" TEXT,
  "price str" TEXT,
  "price range" TEXT,
  "people" INTEGER,
  "hotel amenities" TEXT,
  "location snake" TEXT,
  "location adverb" TEXT,
  "num people" INTEGER,
  "train id" INTEGER,
  "phone number" INTEGER,
  "reference number" INTEGER,
  "num nights" INTEGER,
  "stars" INTEGER,
  "start date" TEXT,
  "guesthouse" TEXT,
  "cuisine" TEXT,
  "moderate price range" TEXT,
  "reference number (restaurant:17)" INTEGER,
  "cheap" TEXT,
  "price range (restaurant:15)" TEXT,
  "restaurant address" TEXT,
  "phone number (restaurant:12)" INTEGER,
  "num table" INTEGER,
  "entry fee" TEXT,
  "location str" TEXT,
  "restaurant name" TEXT,
  "location (restaurant:8)" TEXT,
  "price" TEXT,
  "expensive" TEXT,
  "pickup location" TEXT,
  "table" TEXT,
  "address" TEXT,
  PRIMARY KEY ("reference number key")
);
