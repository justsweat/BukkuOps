## Improvements
`For importing from asoft, figure out only taking the latest changes, especially for products and contacts, so don't need to import whole thing every single time. can make use of DATE_ADD field`

## Pending
-sync changes for invoices daily
account for other stuffs such as contacts, products, etc
as long as there's date modified, then can do..
have to be separate.. since the update is put request

## Sales
- Quotation       : NA - # don't have any quotation in asoft
- Sales Order     : Done `Need Update module`
- Delivery Order  : Done `Need Update module`
- Invoice         : Done `Need Update module`
- Credit Note     : Done `Need Update module`
- Payment         : Created asoft portion, KIv for now since not e-invoice related
- Refund          : Not sure if we're using
- Debit Note      : Done - it's part of invoice `Need Update module`
- CN for Discount : `Think of workflow for this` - omit tiktok and shopee 

## Purchase
- Purchase Order  : Done `Need Update module`
- Goods Received Note: Done `Need Update module`
- Bill            : Done - Supplier Invoice in asoft `Need Update module`
- Credit Note     : Only done asoft, but found no transac for 2025
- Payment         : Done `Need Update module`
- Refund          : Might be NA
- Debit Note      : `No transac in 2025` has to convert from DN to invoice - it's part of invoice

## Bank
- Money In        : `Not Yet` - Not in API, NA as not e-invoice related
- Money Out       : `Not Yet` - Not in API, NA as not e-invoice related
- Transfer        : `Not Yet` - Not in API, NA as not e-invoice related

## Contact
- Contacts        : Done | `Need Update module` `KIV because no TIN on asoft`
- Groups          : Done

## Product
- Product         : Done | Update Module Done
- Groups          : Done

## Accounting
- Journal Entries : Might be NA
- Account         : `Not Yet - might be NA`