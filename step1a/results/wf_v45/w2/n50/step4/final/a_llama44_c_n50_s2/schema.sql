CREATE TABLE "hotel" (
  "reservation number key" INTEGER,
  "start date" TEXT,
  "phone number" INTEGER,
  "num stars" INTEGER,
  "guest house name" TEXT,
  "reservation number" INTEGER,
  "num days" INTEGER,
  "price range str" TEXT,
  "location" TEXT,
  "str" TEXT,
  "people" TEXT,
  "area" TEXT,
  "price range" TEXT,
  "entity" TEXT,
  "num nights" INTEGER,
  "num people" INTEGER,
  "hotel name" TEXT,
  "party size" TEXT,
  "date" TEXT,
  PRIMARY KEY ("reservation number key")
);

CREATE TABLE "train" (
  "id" INTEGER,
  "train id" INTEGER,
  "reference number" INTEGER,
  "day of week str" TEXT,
  "time str" TIME,
  "travel time" TEXT,
  "day of week" TEXT,
  "train id (train:14)" INTEGER,
  "departure location" TEXT,
  "duration str" INTERVAL,
  "time" TIME,
  "location capitalized" TEXT,
  "departure time" INTEGER,
  "total fee" TEXT,
  "currency" NUMERIC(10, 2),
  "departure station" TEXT,
  "location str" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "restaurant" (
  "reference number key" INTEGER,
  "day of week" TEXT,
  "venue name" TEXT,
  "cuisine" TEXT,
  "price range str" TEXT,
  "restaurant name" TEXT,
  "num" INTEGER,
  "str" TEXT,
  "phone number" INTEGER,
  "location abbrev" TEXT,
  "location area" TEXT,
  "date" TEXT,
  "price" TEXT,
  "time int" TIME,
  "location str" TEXT,
  "num str" TEXT,
  "reservation time" INTERVAL,
  "reference number" INTEGER,
  "food type" TEXT,
  "time str" INTEGER,
  "num int" INTEGER,
  "location" TEXT,
  "address" INTEGER,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "attraction" (
  "postcode key" INTEGER,
  "address" TEXT,
  "attraction name" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "street name" TEXT,
  "cinema name" TEXT,
  "location area" TEXT,
  "attraction type" TEXT,
  "location full" TEXT,
  "bed and breakfast" TEXT,
  "location abbr" TEXT,
  "location" TEXT,
  "venue" TEXT,
  "location str" TEXT,
  "favorite museum" TEXT,
  "postcode" INTEGER,
  PRIMARY KEY ("postcode key")
);

CREATE TABLE "attraction_2" (
  "attraction name key" INTEGER,
  "attraction name" TEXT,
  PRIMARY KEY ("attraction name key")
);
