CREATE TABLE "train_schedule" (
  "reference number key" INTEGER,
  "date" TEXT,
  "departure day" TEXT,
  "destination" TEXT,
  "location" TEXT,
  "number of people" INTEGER,
  "price" NUMERIC(10, 2),
  "reference number" TEXT,
  "arrival time" TIME,
  "departure day (train_schedule:13)" TIME,
  "travel time" INTERVAL,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "accommodation_option" (
  "reference number key" INTEGER,
  "address" TEXT,
  "amenity" TEXT,
  "amenity str" TEXT,
  "area" TEXT,
  "checkin date" TEXT,
  "day" TEXT,
  "hotel name" TEXT,
  "hotel type" TEXT,
  "hotel reference" TEXT,
  "num people" INTEGER,
  "rating" TEXT,
  "reference number" INTEGER,
  "hotel type (accommodation_option:19)" TEXT,
  "hotel type (accommodation_option:21)" TEXT,
  "amenities" TEXT,
  "internet" TEXT,
  "parking" TEXT,
  "price_range" TEXT,
  "facilities" TEXT,
  "services" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "location" (
  "id" INTEGER,
  "location" TEXT,
  "location name" TEXT,
  "location part" TEXT,
  "location str" TEXT,
  "lodging type" TEXT,
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
  "phone number" INTEGER,
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
  PRIMARY KEY ("phone_number"),
  FOREIGN KEY ("phone number") REFERENCES "establishment" ("reference number key")
);

CREATE TABLE "location_establishment" (
  "location_establishment id" INTEGER,
  "location id" INTEGER,
  "establishment id" INTEGER,
  PRIMARY KEY ("location_establishment id"),
  FOREIGN KEY ("location id") REFERENCES "location" ("id"),
  FOREIGN KEY ("establishment id") REFERENCES "establishment" ("reference number key")
);
