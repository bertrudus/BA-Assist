# Order Fulfilment Process

## Start Event
Customer places an order via the online bookstore.

## Steps

1. **Receive Order** (System)
   - Order details are recorded in the order management system.
   - Inventory is checked for all items.

2. **Decision: All Items In Stock?**
   - **Yes** → Proceed to step 3.
   - **No** → Proceed to step 2a.

   2a. **Notify Customer of Backorder** (Customer Service)
       - Email customer with expected restock date.
       - Customer chooses to wait or cancel backordered items.

3. **Pick and Pack** (Warehouse Team)
   - Warehouse staff pick items from shelves.
   - Items are packed and labelled with shipping details.

4. **Handoff to Courier** (Warehouse → Logistics)
   - Packed order is handed to the courier partner.
   - Tracking number is generated and recorded.

5. **Update Order Status** (System)
   - Order status updated to "Shipped".
   - Customer receives shipping confirmation email with tracking link.

6. **Delivery** (Courier)
   - Courier delivers the package to the customer address.

7. **Decision: Delivery Successful?**
   - **Yes** → Proceed to step 8.
   - **No** → Proceed to step 7a.

   7a. **Handle Failed Delivery** (Customer Service)
       - Contact customer to arrange re-delivery or collection.

8. **Close Order** (System)
   - Order status updated to "Delivered".
   - Satisfaction survey email sent after 3 days.

## End Event
Order is marked as delivered and closed.
