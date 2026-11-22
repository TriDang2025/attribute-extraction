CREATE TABLE "train_schedule" (
  "reference number key" INTEGER,
  "departure day" TIME,
  "arrival time" TIME,
  "number of people" INTEGER,
  "location" TEXT,
  "price" NUMERIC(10, 2),
  "departure day (train_schedule:4)" TEXT,
  "reference number" TEXT,
  "date" TEXT,
  "destination" TEXT,
  "travel time" INTERVAL,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "accommodation_option" (
  "accommodation_option" INTEGER,
  "hotel type" TEXT,
  "checkin date" TEXT,
  "area" TEXT,
  "lodging type" TEXT,
  "internet" TEXT,
  "hotel type (accommodation_option:21)" TEXT,
  "hotel type (accommodation_option:19)" TEXT,
  "hotel name" TEXT,
  "amenities" TEXT,
  "services" TEXT,
  "address" TEXT,
  "price_range" TEXT,
  "rating" TEXT,
  "parking" TEXT,
  "facilities" TEXT,
  PRIMARY KEY ("accommodation_option")
);

CREATE TABLE "location" (
  "id" INTEGER,
  "location" TEXT,
  "location name" TEXT,
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
  "destination" TEXT,
  "departure location" TEXT,
  "pickup location" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "establishment" (
  "reference number key" INTEGER,
  "college name" TEXT,
  "cuisine" TEXT,
  "reference number" INTEGER,
  "date" TEXT,
  "location" TEXT,
  "cuisine_type" TEXT,
  "number of colleges" INTEGER,
  "restaurant name" TEXT,
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
  "cuisine_type (establishment:24)" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number" (
  "phone_number" INTEGER,
  "phone number" INTEGER,
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
