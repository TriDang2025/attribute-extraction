CREATE TABLE "phone_number" (
  "phone_number" INTEGER,
  "departure time" TIME,
  PRIMARY KEY ("phone_number")
);

CREATE TABLE "accommodation_option" (
  "reference number key" INTEGER,
  "date" TEXT,
  "departure day" TEXT,
  "destination" TEXT,
  "location" TEXT,
  "number of people" INTEGER,
  "price" NUMERIC(10, 2),
  "reference number" TEXT,
  "time int" TIME,
  "time str" TIME,
  "travel time" INTERVAL,
  "address" TEXT,
  "amenity" TEXT,
  "amenity str" TEXT,
  "area" TEXT,
  "checkin date" TEXT,
  "day" TEXT,
  "hotel name" TEXT,
  "hotel rating" INTEGER,
  "hotel reference" TEXT,
  "location (accommodation_option:10)" TEXT,
  "location name" TEXT,
  "location part" TEXT,
  "location str" TEXT,
  "lodging type" TEXT,
  "num people" INTEGER,
  "rating" TEXT,
  "reference number (accommodation_option:18)" INTEGER,
  "str" TEXT,
  "time" TIME,
  "type" TEXT,
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
  "address" INTEGER,
  "college" TEXT,
  "entrance fee" TEXT,
  "location" TEXT,
  "museum" TEXT,
  "park" TEXT,
  "phone number" INTEGER,
  "theatre" INTEGER,
  "postcode" INTEGER,
  "time" TIME,
  "arrival time" TIME,
  "day of week" TEXT,
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
  "price" TEXT,
  "price range" TEXT,
  "reference number" INTEGER,
  "restaurant info" TEXT,
  "restaurant name" TEXT,
  "something" TEXT,
  "str" TEXT,
  "table booking" TEXT,
  "table reservation time" INTERVAL,
  "cuisine_type" TEXT,
  "cuisine_type (establishment:25)" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number_2" (
  "phone_number" INTEGER,
  "phone number" INTEGER,
  "phone number (establishment:12)" INTEGER,
  "departure location" TEXT,
  "destination" TEXT,
  "party size" INTEGER,
  "pickup location" TEXT,
  "time str" INTEGER,
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
