CREATE TABLE "hotel" (
  "reservation number key" INTEGER,
  "str" TEXT,
  "hotel name" TEXT,
  "num people" INTEGER,
  "party size" TEXT,
  "area" TEXT,
  "reservation number" INTEGER,
  "location" TEXT,
  "num stars" INTEGER,
  "num days" INTEGER,
  "price range" TEXT,
  "price range str" TEXT,
  "entity" TEXT,
  "num nights" INTEGER,
  "date" TEXT,
  "guest house name" TEXT,
  PRIMARY KEY ("reservation number key")
);

CREATE TABLE "train" (
  "id" INTEGER,
  "train id" INTEGER,
  "departure station" TEXT,
  "location capitalized" TEXT,
  "day of week str" TEXT,
  "duration str" INTERVAL,
  "train id (train:14)" INTEGER,
  "total fee" TEXT,
  "departure location" TEXT,
  "travel time" TEXT,
  "location str" TEXT,
  "time" TIME,
  "time str" TIME,
  "currency" NUMERIC(10, 2),
  "departure time" INTEGER,
  "day of week" TEXT,
  "reference number" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "restaurant" (
  "reference number key" INTEGER,
  "location str" TEXT,
  "time int" TIME,
  "num" INTEGER,
  "date" TEXT,
  "location" TEXT,
  "venue name" TEXT,
  "cuisine" TEXT,
  "location abbrev" TEXT,
  "address" INTEGER,
  "food type" TEXT,
  "phone number" INTEGER,
  "day of week" TEXT,
  "num int" INTEGER,
  "restaurant name" TEXT,
  "num str" TEXT,
  "time str" INTEGER,
  "reservation time" INTERVAL,
  "price range str" TEXT,
  "price" TEXT,
  "location area" TEXT,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "attraction" (
  "attraction name key" INTEGER,
  "attraction name" TEXT,
  "address" TEXT,
  "location full" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "location area" TEXT,
  "location" TEXT,
  "attraction type" TEXT,
  "cinema name" TEXT,
  "bed and breakfast" TEXT,
  "postcode" INTEGER,
  "favorite museum" TEXT,
  "location abbr" TEXT,
  "street name" TEXT,
  "location str" TEXT,
  "venue" TEXT,
  PRIMARY KEY ("attraction name key")
);

CREATE TABLE "attraction_2" (
  "attraction name key" INTEGER,
  "attraction name" TEXT,
  PRIMARY KEY ("attraction name key")
);
