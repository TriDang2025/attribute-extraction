CREATE TABLE "train" (
  "Train arrive by" TIME,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train duration" INTERVAL,
  "Train leave at" TIME,
  "Train price" NUMERIC(10, 2),
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  PRIMARY KEY ("Train confirmed reference")
);

CREATE TABLE "hotel" (
  "hotel id" INTEGER,
  "Hotel confirmed reference" INTEGER,
  "Hotel name" TEXT,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  "Hotel stars" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant" (
  "Restaurant confirmed reference" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("Restaurant confirmed reference")
);

CREATE TABLE "hotel_booking" (
  "Hotel address" TEXT,
  "Hotel area" TEXT,
  "Hotel phone" INTEGER,
  "Hotel postcode" INTEGER,
  "Hotel price range" TEXT,
  "Hotel type" TEXT,
  "Restaurant address" TEXT,
  "Restaurant area" TEXT,
  "Restaurant food" TEXT,
  "Restaurant name" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant postcode" INTEGER,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("Restaurant phone")
);
