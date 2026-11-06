CREATE TABLE "train" (
  "Train arrive by" TIME,
  "Train day" TEXT,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train leave at" TIME,
  "Train duration" TEXT,
  "Train price" REAL,
  "Train trainid" TEXT,
  PRIMARY KEY ("Train trainid")
);

CREATE TABLE "train_booking" (
  "Train booking id" TEXT,
  "Train booking trainid" TEXT,
  "Train confirmed reference" TEXT,
  "Train requested people" INTEGER,
  PRIMARY KEY ("Train booking id"),
  FOREIGN KEY ("Train booking trainid") REFERENCES "train" ("Train trainid")
);

CREATE TABLE "hotel" (
  "Hotel area" TEXT,
  "Hotel internet" TEXT,
  "Hotel name" TEXT,
  "Hotel parking" TEXT,
  "Hotel price range" TEXT,
  "Hotel stars" INTEGER,
  "Hotel type" TEXT,
  "Hotel address" TEXT,
  "Hotel phone" INTEGER,
  "Hotel postcode" TEXT,
  PRIMARY KEY ("Hotel name")
);

CREATE TABLE "hotel_booking" (
  "Hotel booking id" TEXT,
  "Hotel confirmed name" TEXT,
  "Hotel confirmed reference" TEXT,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  PRIMARY KEY ("Hotel booking id"),
  FOREIGN KEY ("Hotel confirmed name") REFERENCES "hotel" ("Hotel name")
);

CREATE TABLE "restaurant" (
  "Restaurant area" TEXT,
  "Restaurant food" TEXT,
  "Restaurant name" TEXT,
  "Restaurant price range" TEXT,
  "Restaurant address" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant postcode" TEXT,
  PRIMARY KEY ("Restaurant name")
);

CREATE TABLE "restaurant_booking" (
  "Restaurant booking id" TEXT,
  "Restaurant confirmed name" TEXT,
  "Restaurant confirmed reference" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("Restaurant booking id"),
  FOREIGN KEY ("Restaurant confirmed name") REFERENCES "restaurant" ("Restaurant name")
);

CREATE TABLE "taxi" (
  "Taxi ride id" TEXT,
  "Taxi arrive by" TIME,
  "Taxi departure" TEXT,
  "Taxi destination" TEXT,
  "Taxi leave at" TIME,
  "Taxi phone" INTEGER,
  "Taxi type" TEXT,
  PRIMARY KEY ("Taxi ride id")
);

CREATE TABLE "attraction" (
  "Attraction area" TEXT,
  "Attraction name" TEXT,
  "Attraction type" TEXT,
  "Attraction address" TEXT,
  "Attraction entrancefee" TEXT,
  "Attraction openhours" TEXT,
  "Attraction phone" INTEGER,
  "Attraction postcode" TEXT,
  PRIMARY KEY ("Attraction name")
);
