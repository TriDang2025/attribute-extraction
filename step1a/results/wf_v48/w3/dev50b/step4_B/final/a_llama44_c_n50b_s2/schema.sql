CREATE TABLE "train_schedule" (
  "reference number key" INTEGER,
  "time int" TIME,
  "number of people" INTEGER,
  "price" NUMERIC(10, 2),
  "departure day" TEXT,
  "reference number" TEXT,
  "date" TEXT,
  "destination" TEXT,
  "travel time" INTERVAL,
  "day of week" TIME,
  "table reservation time" INTERVAL,
  "time" TIME,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "accommodation_option" (
  "accommodation_option" INTEGER,
  "time str" TIME,
  "hotel rating" INTEGER,
  "checkin date" TEXT,
  "area" TEXT,
  "lodging type" TEXT,
  "type" TEXT,
  "str" TEXT,
  "time" TIME,
  "hotel name" TEXT,
  "day" TEXT,
  "amenities" TEXT,
  "services" TEXT,
  "rating" TEXT,
  "parking" TEXT,
  "facilities" TEXT,
  PRIMARY KEY ("accommodation_option")
);

CREATE TABLE "location" (
  "id" INTEGER,
  "location" TEXT,
  "location name" TEXT,
  "amenity str" TEXT,
  "location str" TEXT,
  "location part" TEXT,
  "address" INTEGER,
  "theatre" INTEGER,
  "location (location:4)" TEXT,
  "college" TEXT,
  "phone number" INTEGER,
  "museum" TEXT,
  "park" TEXT,
  "entrance fee" TEXT,
  "location str (establishment:8)" TEXT,
  "day of week" TEXT,
  "party size" INTEGER,
  "destination" TEXT,
  "departure location" TEXT,
  "pickup location" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "establishment" (
  "reference number key" INTEGER,
  "phone number" INTEGER,
  "address" TEXT,
  "amenity" TEXT,
  "hotel reference" TEXT,
  "price_range" TEXT,
  "num people" INTEGER,
  "reference number" INTEGER,
  "college name" TEXT,
  "cuisine" TEXT,
  "reference number (establishment:16)" INTEGER,
  "date" TEXT,
  "location" TEXT,
  "cuisine_type" TEXT,
  "number of colleges" INTEGER,
  "restaurant name" TEXT,
  "price" TEXT,
  "str" TEXT,
  "entity" TEXT,
  "num people (establishment:9)" INTEGER,
  "party size" INTEGER,
  "postcode" INTEGER,
  "entrance fee" NUMERIC(10, 2),
  "price range" TEXT,
  "table booking" TEXT,
  "something" TEXT,
  "phone number (establishment:12)" INTEGER,
  "restaurant info" TEXT,
  "cuisine_type (establishment:24)" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number" (
  "phone_number" INTEGER,
  "arrival time" TIME,
  "time str" INTEGER,
  "departure time" TIME,
  "contact_number" TEXT,
  PRIMARY KEY ("phone_number")
);

CREATE TABLE "location_establishment" (
  "location_establishment id" INTEGER,
  "location id" INTEGER,
  "establishment id" INTEGER,
  PRIMARY KEY ("location_establishment id"),
  FOREIGN KEY ("location id") REFERENCES "location" ("id"),
  FOREIGN KEY ("establishment id") REFERENCES "establishment" ("reference number key")
);
