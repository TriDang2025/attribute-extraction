CREATE TABLE "hotel" (
  "reservation number key" INTEGER,
  "area" TEXT,
  "date" TEXT,
  "entity" TEXT,
  "guest house name" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "num days" INTEGER,
  "num nights" INTEGER,
  "num people" INTEGER,
  "num stars" INTEGER,
  "party size" TEXT,
  "price range" TEXT,
  "price range str" TEXT,
  "reservation number" INTEGER,
  "str" TEXT,
  "train id" INTEGER,
  PRIMARY KEY ("reservation number key")
);

CREATE TABLE "train" (
  "train id key" INTEGER,
  "currency" NUMERIC(10, 2),
  "day of week" TEXT,
  "day of week str" TEXT,
  "departure location" TEXT,
  "departure station" TEXT,
  "departure time" INTEGER,
  "duration str" INTERVAL,
  "location capitalized" TEXT,
  "location str" TEXT,
  "reference number" INTEGER,
  "time" TIME,
  "time str" TIME,
  "total fee" TEXT,
  "train id" INTEGER,
  "travel time" TEXT,
  PRIMARY KEY ("train id key")
);

CREATE TABLE "restaurant" (
  "id" INTEGER,
  "address" INTEGER,
  "cuisine" TEXT,
  "date" TEXT,
  "day of week" TEXT,
  "food type" TEXT,
  "location" TEXT,
  "location abbrev" TEXT,
  "location area" TEXT,
  "location str" TEXT,
  "num" INTEGER,
  "num int" INTEGER,
  "num str" TEXT,
  "phone number" INTEGER,
  "price" TEXT,
  "price range str" TEXT,
  "reference number" INTEGER,
  "reservation time" INTERVAL,
  "restaurant name" TEXT,
  "time int" TIME,
  "time str" INTEGER,
  "venue name" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "attraction" (
  "name id" INTEGER,
  "address" TEXT,
  "attraction name" TEXT,
  "attraction type" TEXT,
  "bed and breakfast" TEXT,
  "cinema name" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "favorite museum" TEXT,
  "location" TEXT,
  "location abbr" TEXT,
  "location area" TEXT,
  "location full" TEXT,
  "location str" TEXT,
  "postcode" INTEGER,
  "street name" TEXT,
  "venue" TEXT,
  PRIMARY KEY ("name id")
);

CREATE TABLE "attraction_2" (
  "attraction name key" INTEGER,
  "attraction name" TEXT,
  PRIMARY KEY ("attraction name key")
);
