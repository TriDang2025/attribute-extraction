CREATE TABLE "hotel" (
  "reference number key" INTEGER,
  "area" TEXT,
  "date" TEXT,
  "entity" TEXT,
  "guest house name" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "num days" INTEGER,
  "num nights" INTEGER,
  "num people" INTEGER,
  "party size" TEXT,
  "price" TEXT,
  "price range" TEXT,
  "price range str" TEXT,
  "reference number" INTEGER,
  "start date" TEXT,
  "str" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "train" (
  "train id key" INTEGER,
  "day of week" TEXT,
  "day of week str" TEXT,
  "departure location" TEXT,
  "departure station" TEXT,
  "departure time" INTEGER,
  "duration str" INTERVAL,
  "location str" TEXT,
  "price" NUMERIC(10, 2),
  "stansted airport" TEXT,
  "time" TIME,
  "time str" INTEGER,
  "total fee" TEXT,
  "train id" TIME,
  "travel time" TEXT,
  PRIMARY KEY ("train id key")
);

CREATE TABLE "restaurant" (
  "restaurant name key" INTEGER,
  "address" TEXT,
  "cuisine" TEXT,
  "date" TEXT,
  "location" TEXT,
  "location area" TEXT,
  "location str" TEXT,
  "num" INTEGER,
  "num card" INTEGER,
  "num ord" INTEGER,
  "num str" INTEGER,
  "phone number" INTEGER,
  "price range" TEXT,
  "price range str" TEXT,
  "reference number" INTEGER,
  "reservation time" INTERVAL,
  "restaurant name" TEXT,
  "str" TEXT,
  "time int" TIME,
  "time str" TIME,
  "venue name" TEXT,
  PRIMARY KEY ("restaurant name key")
);

CREATE TABLE "attraction" (
  "postcode key" INTEGER,
  "address" TEXT,
  "attraction name" TEXT,
  "attraction type" TEXT,
  "bed and breakfast" TEXT,
  "cinema name" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "favorite museum" TEXT,
  "location" TEXT,
  "location full" TEXT,
  "location str" TEXT,
  "postcode" INTEGER,
  "street name" TEXT,
  "venue" TEXT,
  PRIMARY KEY ("postcode key")
);

CREATE TABLE "attraction_2" (
  "attraction name key" INTEGER,
  "attraction name" TEXT,
  PRIMARY KEY ("attraction name key")
);
