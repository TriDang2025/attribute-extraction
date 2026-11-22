CREATE TABLE "location" (
  "reference number key" INTEGER,
  "location" TEXT,
  "location name" TEXT,
  "amenity str" TEXT,
  "location str" TEXT,
  "hotel name" TEXT,
  "phone number" INTEGER,
  "amenities" TEXT,
  "services" TEXT,
  "address" TEXT,
  "amenity" TEXT,
  "hotel reference" TEXT,
  "price_range" TEXT,
  "num people" INTEGER,
  "reference number" INTEGER,
  "location part" TEXT,
  "arrival time" TIME,
  "day of week" TEXT,
  "party size" INTEGER,
  "destination" TEXT,
  "departure location" TEXT,
  "pickup location" TEXT,
  "internet" TEXT,
  "hotel type" TEXT,
  "hotel type (accommodation_option:19)" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "establishment" (
  "name id" INTEGER,
  "entity" TEXT,
  "location str" TEXT,
  "num people" INTEGER,
  "party size" INTEGER,
  "table reservation time" INTERVAL,
  "postcode" INTEGER,
  "entrance fee" NUMERIC(10, 2),
  "price range" TEXT,
  "table booking" TEXT,
  "time" TIME,
  "something" TEXT,
  "phone number" INTEGER,
  "restaurant info" TEXT,
  "cuisine_type" TEXT,
  "contact_number" TEXT,
  PRIMARY KEY ("name id")
);

CREATE TABLE "phone_number" (
  "phone_number" INTEGER,
  "time str" INTEGER,
  "departure time" TIME,
  PRIMARY KEY ("phone_number")
);

CREATE TABLE "location_establishment" (
  "location_establishment id" INTEGER,
  "location id" INTEGER,
  "establishment id" INTEGER,
  PRIMARY KEY ("location_establishment id"),
  FOREIGN KEY ("location id") REFERENCES "location" ("reference number key"),
  FOREIGN KEY ("establishment id") REFERENCES "establishment" ("name id")
);
