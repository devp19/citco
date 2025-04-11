# Project CITCO (NSERC Discovery Grant Analysis)
CPS406 (Software Engineering) | Sprint 3 Executable Code for Citco (NSERC DG)

### Project Overview

Citco is a web application that investigates whether there's a correlation between individual
researchers’ citation counts and the amount of money they have been granted through their respective
Discovery Grants (DGs) through the Natural Sciences and Engineering Research Council of Canada
(NSERC). Users will be able to filter and display the gathered information using a variety of graphs
and data visualizations, enhanced with customizable colour schemes. 

Our primary focus is on Canadian computer science researchers. We sourced data from NSERC’s grant
database and Google Scholar’s citation records, enabling us to create visualizations that examine 
trends in citation activity and grant amounts over the past 15 years.

Our analysis reveals that, overall, there is little evidence of a strong relationship between 
DG amounts and citation counts, as shown by a <em>Pearson correlation coefficient</em> of 
approximately <em>0.3</em>, a value near zero. However, when examining the data at a more granular 
level, we find that citation metrics can offer meaningful insights into funding outcomes at specific universities.

<strong><em>*It's important to consider dataset filters directly from NSERC as results may vary slightly 
depending on the specifications provided when downloading the dataset.</em></strong>

---

### Team Members
>Jainam Shah  
>Hamza Yalcin  
>Sadiksha Dahal  
>Neeti Dhiman  
>Jonathan Thomas   
>Dev Patel

---

### Technology Stack

- Python (Webscraping and Data Visualization)
- Flask (Rendering Dashboard)
- JavaScript (Functionality)
- HTML/CSS (User Interface)
- Libraries:

  >Pandas
  >numpy
  >Matplitlib
  >BeautifulSoup  
  >urlib.prase  
  >requests  

---

### Initial Setup

*Important to list out dataset filters as results may slightly vary depending on specifications provided when recieving dataset from NSERC!*

**Dataset Filters:**
> Fiscal Year (From): 2010-2011  
> Fiscal Year (To): 2023-2024  
> Keywords in: Discovery  
> Area of Application: Information, computer and communication technologies  
> By Institutions: All
>
> 

---

### Example of Usage

**Filter: All years at all universities**

<img width="1469" alt="Screenshot 2025-04-10 at 10 50 06 PM" src="https://github.com/user-attachments/assets/6fe0373d-6ef0-47e2-9b0c-954d931f1bec" />  

  
**Filter: All years at Waterloo University**

<img width="1470" alt="Screenshot 2025-04-10 at 10 49 22 PM" src="https://github.com/user-attachments/assets/95b3b557-29d6-4b8f-8019-7bab718bb1bd" />
