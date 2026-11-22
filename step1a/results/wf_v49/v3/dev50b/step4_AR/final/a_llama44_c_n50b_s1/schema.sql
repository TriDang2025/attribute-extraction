CREATE TABLE "train" (
  "reference number key" INTEGER,
  "date" TEXT,
  "location" TEXT,
  "destination" TEXT,
  "departure day" TEXT,
  "price" NUMERIC(10, 2),
  "number of people" INTEGER,
  "time int" TIME,
  "travel time" INTERVAL,
  "time str" TIME,
  "reference number" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "accommodation" (
  "accommodation_option" INTEGER,
  "parking" TEXT,
  "amenity str" TEXT,
  "location part" TEXT,
  "amenity" TEXT,
  PRIMARY KEY ("accommodation_option")
);

CREATE TABLE "location" (
  "location key" INTEGER,
  "location" TEXT,
  "location str" TEXT,
  "address" TEXT,
  "museum" TEXT,
  "park" TEXT,
  "college" TEXT,
  "entrance fee" TEXT,
  "location (location:4)" TEXT,
  "theatre" INTEGER,
  "location (establishment:7)" TEXT,
  "location str (establishment:8)" TEXT,
  "postcode" INTEGER,
  "pickup location" TEXT,
  "destination" TEXT,
  PRIMARY KEY ("location key")
);

CREATE TABLE "establishment" (
  "reference_number" INTEGER,
  "lodging type" TEXT,
  "phone number" INTEGER,
  "address" INTEGER,
  "time" TIME,
  "price range" TEXT,
  "date" TEXT,
  "cuisine" TEXT,
  "phone number (establishment:12)" INTEGER,
  "college name" TEXT,
  "str" TEXT,
  "entity" TEXT,
  "something" TEXT,
  "cuisine_type" TEXT,
  "reference number" INTEGER,
  "num people" INTEGER,
  "cuisine_type (establishment:25)" TEXT,
  "restaurant info" TEXT,
  "party size" INTEGER,
  "table reservation time" INTERVAL,
  "number of colleges" INTEGER,
  "entrance fee" NUMERIC(10, 2),
  "day of week" TIME,
  "table booking" TEXT,
  "restaurant name" TEXT,
  "price" TEXT,
  PRIMARY KEY ("reference_number"),
  FOREIGN KEY ("address") REFERENCES "location" ("location key")
);

CREATE TABLE "phone_number" (
  "phone number" INTEGER,
  "contact_number" TEXT,
  "departure location" TEXT,
  "time str" INTEGER,
  PRIMARY KEY ("contact_number"),
  FOREIGN KEY ("contact_number") REFERENCES "establishment" ("reference_number")
);
