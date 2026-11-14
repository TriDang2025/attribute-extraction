CREATE TABLE "train" (
  "Train leave at" TIME,
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  "Train price" NUMERIC(10, 2),
  "Restaurant food" TEXT,
  "Restaurant requested time" TIME,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant requested day" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("Train trainid")
);

CREATE TABLE "hotel" (
  "hotel name id" INTEGER,
  "Train departure" TEXT,
  "Train arrive by" TIME,
  "Train destination" TEXT,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel type" TEXT,
  "Hotel stars" INTEGER,
  "Hotel name" TEXT,
  "Hotel requested day" TEXT,
  "Hotel price range" TEXT,
  "Hotel phone" INTEGER,
  "Hotel requested stay" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("hotel name id")
);

CREATE TABLE "restaurant" (
  "restaurant id" INTEGER,
  "Restaurant phone" INTEGER,
  "Restaurant price range" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant name" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("restaurant id")
);

CREATE TABLE "hotel_booking" (
  "Hotel address" TEXT,
  "Hotel area" TEXT,
  "Hotel confirmed reference" INTEGER,
  "Restaurant area" TEXT,
  "Restaurant address" TEXT,
  PRIMARY KEY ("Hotel confirmed reference")
);
