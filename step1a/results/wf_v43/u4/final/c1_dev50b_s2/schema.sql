CREATE TABLE "train" (
  "trainid" INTEGER,
  "Train duration" INTERVAL,
  "Train trainid" INTEGER,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train leave at" TIME,
  "Train price" NUMERIC(10, 2),
  "Train day" TEXT,
  "Train requested people" INTEGER,
  "Train confirmed reference" INTEGER,
  "Train arrive by" TIME,
  PRIMARY KEY ("trainid")
);

CREATE TABLE "hotel" (
  "confirmed reference" INTEGER,
  "Hotel area" TEXT,
  "Hotel phone" INTEGER,
  "Hotel stars" INTEGER,
  "Hotel requested people" INTEGER,
  "Hotel postcode" INTEGER,
  "Hotel confirmed reference" INTEGER,
  "Hotel name" TEXT,
  "Hotel requested stay" INTEGER,
  "Hotel requested day" TEXT,
  "Hotel type" TEXT,
  "Hotel address" TEXT,
  "Hotel price range" TEXT,
  PRIMARY KEY ("confirmed reference")
);

CREATE TABLE "restaurant" (
  "description" INTEGER,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant address" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant area" TEXT,
  "Restaurant food" TEXT,
  "Restaurant price range" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant requested time" TIME,
  "Restaurant postcode" TEXT,
  "Restaurant name" TEXT,
  PRIMARY KEY ("description")
);
