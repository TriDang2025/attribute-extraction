CREATE TABLE "train_schedule" (
  "time int key" INTEGER,
  "price" NUMERIC(10, 2),
  "number of people" INTEGER,
  "time int" TIME,
  "travel time" INTERVAL,
  "time str" TIME,
  PRIMARY KEY ("time int key")
);

CREATE TABLE "accommodation_option" (
  "reference number key" INTEGER,
  "checkin date" TEXT,
  "facilities" TEXT,
  "day" TEXT,
  "reference number" INTEGER,
  "hotel name" TEXT,
  "price_range" TEXT,
  "type" TEXT,
  "rating" TEXT,
  "amenities" TEXT,
  "internet" TEXT,
  "str" TEXT,
  "hotel rating" INTEGER,
  "hotel reference" TEXT,
  "num people" INTEGER,
  "services" TEXT,
  "time" TIME,
  "lodging type" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "location" (
  "id" INTEGER,
  "date" TEXT,
  "location" TEXT,
  "destination" TEXT,
  "departure day" TEXT,
  "location (accommodation_option:10)" TEXT,
  "location name" TEXT,
  "area" TEXT,
  "location str" TEXT,
  "address" TEXT,
  "address (location:1)" INTEGER,
  "museum" TEXT,
  "park" TEXT,
  "college" TEXT,
  "location (location:4)" TEXT,
  "theatre" INTEGER,
  "pickup location" TEXT,
  "destination (phone_number:6)" TEXT,
  "day of week" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "establishment" (
  "reference number key" INTEGER,
  "reference number" TEXT,
  "entrance fee" TEXT,
  "time" TIME,
  "price range" TEXT,
  "date" TEXT,
  "cuisine" TEXT,
  "college name" TEXT,
  "str" TEXT,
  "location" TEXT,
  "location str" TEXT,
  "postcode" INTEGER,
  "entity" TEXT,
  "something" TEXT,
  "cuisine_type" TEXT,
  "reference number (establishment:16)" INTEGER,
  "num people" INTEGER,
  "cuisine_type (establishment:25)" TEXT,
  "restaurant info" TEXT,
  "party size" INTEGER,
  "table reservation time" INTERVAL,
  "number of colleges" INTEGER,
  "entrance fee (establishment:6)" NUMERIC(10, 2),
  "day of week" TIME,
  "table booking" TEXT,
  "restaurant name" TEXT,
  "price" TEXT,
  "party size (phone_number:7)" INTEGER,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number" (
  "phone_number" INTEGER,
  "parking" TEXT,
  "location part" TEXT,
  "phone number" INTEGER,
  "phone number (location:7)" INTEGER,
  "phone number (establishment:12)" INTEGER,
  "contact_number" TEXT,
  "departure location" TEXT,
  "arrival time" TIME,
  "time str" INTEGER,
  "departure time" TIME,
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
