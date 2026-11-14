CREATE TABLE "train" (
  "trainid" INTEGER,
  "Train leave at" TIME,
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  "Train price" NUMERIC(10, 2),
  "Train departure" TEXT,
  "Train arrive by" TIME,
  "Train destination" TEXT,
  "Train day" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("trainid")
);

CREATE TABLE "hotel" (
  "hotel id" INTEGER,
  "Hotel requested people" INTEGER,
  "Hotel type" TEXT,
  "Hotel stars" INTEGER,
  "Hotel name" TEXT,
  "Hotel requested day" TEXT,
  "Hotel price range" TEXT,
  "Hotel phone" INTEGER,
  "Hotel area" TEXT,
  "Hotel confirmed reference" INTEGER,
  "Hotel requested stay" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant" (
  "Restaurant food" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant area" TEXT,
  "Restaurant requested time" TIME,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant address" TEXT,
  "Restaurant name" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("Restaurant food")
);
