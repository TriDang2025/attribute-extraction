CREATE TABLE "hotel" (
  "hotel name key" INTEGER,
  "num days" INTEGER,
  "location" TEXT,
  "area" TEXT,
  "price range" TEXT,
  "entity" TEXT,
  "num nights" INTEGER,
  "num people" INTEGER,
  "hotel name" TEXT,
  "date" TEXT,
  PRIMARY KEY ("hotel name key")
);

CREATE TABLE "train" (
  "train id key" INTEGER,
  "stansted airport" TEXT,
  "day of week str" TEXT,
  "time str" INTEGER,
  "travel time" TEXT,
  "day of week" TEXT,
  "train id" TIME,
  "departure location" TEXT,
  "duration str" INTERVAL,
  "time" TIME,
  "location str" TEXT,
  "departure time" INTEGER,
  "total fee" TEXT,
  "departure station" TEXT,
  "price" NUMERIC(10, 2),
  PRIMARY KEY ("train id key")
);

CREATE TABLE "restaurant" (
  "reference number key" INTEGER,
  "location" TEXT,
  "venue name" TEXT,
  "cuisine" TEXT,
  "price range str" TEXT,
  "reservation time" INTERVAL,
  "restaurant name" TEXT,
  "num str" INTEGER,
  "str" TEXT,
  "price range" TEXT,
  "num" INTEGER,
  "num card" INTEGER,
  "date" TEXT,
  "reference number" INTEGER,
  "time int" TIME,
  "num ord" INTEGER,
  "location area" TEXT,
  "time str" TIME,
  "phone number" INTEGER,
  "location str" TEXT,
  "address" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "attraction" (
  "postcode key" INTEGER,
  "address" TEXT,
  "attraction name" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "street name" TEXT,
  "cinema name" TEXT,
  "location str" TEXT,
  "attraction type" TEXT,
  "postcode" INTEGER,
  "bed and breakfast" TEXT,
  "location full" TEXT,
  "location" TEXT,
  "favorite museum" TEXT,
  "venue" TEXT,
  PRIMARY KEY ("postcode key")
);

CREATE TABLE "attraction_2" (
  "attraction name key" INTEGER,
  "attraction name" TEXT,
  PRIMARY KEY ("attraction name key")
);
