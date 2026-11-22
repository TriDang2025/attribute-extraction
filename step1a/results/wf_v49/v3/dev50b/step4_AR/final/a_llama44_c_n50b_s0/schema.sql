CREATE TABLE "train_schedule" (
  "reference number key" INTEGER,
  "date" TEXT,
  "departure day" TEXT,
  "destination" TEXT,
  "number of people" INTEGER,
  "price" NUMERIC(10, 2),
  "reference number" TEXT,
  "time int" TIME,
  "time str" TIME,
  "travel time" INTERVAL,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "accommodation_option" (
  "accommodation_option" INTEGER,
  "address" TEXT,
  "amenity" TEXT,
  "amenity str" TEXT,
  "area" TEXT,
  "price_range" TEXT,
  "facilities" TEXT,
  "services" TEXT,
  PRIMARY KEY ("accommodation_option")
);

CREATE TABLE "location" (
  "id" INTEGER,
  "location" TEXT,
  "location (accommodation_option:10)" TEXT,
  "location name" TEXT,
  "location part" TEXT,
  "location str" TEXT,
  "lodging type" TEXT,
  "type" TEXT,
  "amenities" TEXT,
  "internet" TEXT,
  "parking" TEXT,
  "address" INTEGER,
  "college" TEXT,
  "entrance fee" TEXT,
  "location (location:4)" TEXT,
  "museum" TEXT,
  "park" TEXT,
  "phone number" INTEGER,
  "theatre" INTEGER,
  "postcode" INTEGER,
  "departure location" TEXT,
  "departure time" TIME,
  "destination" TEXT,
  "pickup location" TEXT,
  "contact_number" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "establishment" (
  "reference number key" INTEGER,
  "college name" TEXT,
  "cuisine" TEXT,
  "date" TEXT,
  "day of week" TIME,
  "entity" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "location" TEXT,
  "location str" TEXT,
  "num people" INTEGER,
  "number of colleges" INTEGER,
  "party size" INTEGER,
  "price range" TEXT,
  "reference number" INTEGER,
  "restaurant name" TEXT,
  "table booking" TEXT,
  "table reservation time" INTERVAL,
  "time" TIME,
  "cuisine_type" TEXT,
  "cuisine_type (establishment:25)" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number" (
  "phone_number" INTEGER,
  "phone number" INTEGER,
  "arrival time" TIME,
  "day of week" TEXT,
  PRIMARY KEY ("phone_number")
);
