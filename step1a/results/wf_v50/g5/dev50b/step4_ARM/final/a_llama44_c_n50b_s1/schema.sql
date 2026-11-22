CREATE TABLE "location" (
  "location key" INTEGER,
  "location str" TEXT,
  "address" TEXT,
  "museum" TEXT,
  "park" TEXT,
  "college" TEXT,
  "entrance fee" TEXT,
  "location" TEXT,
  "theatre" INTEGER,
  "location (establishment:7)" TEXT,
  "location str (establishment:8)" TEXT,
  PRIMARY KEY ("location key")
);

CREATE TABLE "establishment" (
  "reference number key" INTEGER,
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
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number" (
  "phone_number id" INTEGER,
  "contact_number" TEXT,
  "departure location" TEXT,
  "establishment id" INTEGER,
  PRIMARY KEY ("phone_number id"),
  FOREIGN KEY ("establishment id") REFERENCES "establishment" ("reference number key")
);

CREATE TABLE "location_establishment" (
  "location_establishment id" INTEGER,
  "location id" INTEGER,
  "establishment id" INTEGER,
  PRIMARY KEY ("location_establishment id"),
  FOREIGN KEY ("location id") REFERENCES "location" ("location key"),
  FOREIGN KEY ("establishment id") REFERENCES "establishment" ("reference number key")
);
