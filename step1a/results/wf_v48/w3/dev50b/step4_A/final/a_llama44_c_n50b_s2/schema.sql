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
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "accommodation_option" (
  "accommodation_option" INTEGER,
  "hotel rating" INTEGER,
  "checkin date" TEXT,
  "area" TEXT,
  "lodging type" TEXT,
  PRIMARY KEY ("accommodation_option")
);

CREATE TABLE "location" (
  "location key" INTEGER,
  "location" TEXT,
  "location name" TEXT,
  "location str" TEXT,
  "location part" TEXT,
  "location (location:4)" TEXT,
  "museum" TEXT,
  "park" TEXT,
  "destination" TEXT,
  "departure location" TEXT,
  "pickup location" TEXT,
  PRIMARY KEY ("location key")
);

CREATE TABLE "establishment" (
  "reference number key" INTEGER,
  "address" INTEGER,
  "phone number" INTEGER,
  "reference number" INTEGER,
  "location" TEXT,
  "restaurant name" TEXT,
  "entity" TEXT,
  "location str" TEXT,
  "num people" INTEGER,
  "party size" INTEGER,
  "table reservation time" INTERVAL,
  "postcode" INTEGER,
  "price range" TEXT,
  "table booking" TEXT,
  "time" TIME,
  "cuisine_type" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number" (
  "phone_number" INTEGER,
  "contact_number" TEXT,
  PRIMARY KEY ("phone_number")
);

CREATE TABLE "accommodation_option_location" (
  "accommodation_option_location id" INTEGER,
  "accommodation_option id" INTEGER,
  "location id" INTEGER,
  PRIMARY KEY ("accommodation_option_location id"),
  FOREIGN KEY ("accommodation_option id") REFERENCES "accommodation_option" ("accommodation_option"),
  FOREIGN KEY ("location id") REFERENCES "location" ("location key")
);
