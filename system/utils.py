import maya.cmds as mc
import maya.mel as mel
from math import pow, sqrt
import json
import tempfile
import os

def writeJson(fileName, data):
    with open(fileName, 'w') as outfile:
        json.dump(data, outfile)
    file.close(outfile)

def readJson(fileName):
    with open(fileName, 'r') as infile:
        data = (open(infile.name, 'r').read())
    return data

#turns a string into a list with the string being the only object in that list
def stringIntoList(x):
    if isinstance(x, basestring) == True:
        x = [x]

    return x

# function to get the top node of an object
def getRoot(object):
    # set upParent to be object so the loop can start with it
    upParent = object

    # while the upParent has a parent, set the upParent to be the parent.
    while (True):
        theParent = mc.listRelatives(upParent, p=True)

        if not theParent:
            break;

        upParent = theParent[0]

    return upParent

#Credit to Tim Callaway for this function
def getDistance(objA, objB):
    gObjA = mc.xform(objA, q=True, t=True, ws=True)
    gObjB = mc.xform(objB, q=True, t=True, ws=True)

    #distance formula in 3 dimensions
    return sqrt(pow(gObjA[0] - gObjB[0], 2) + pow(gObjA[1] - gObjB[1], 2) + pow(gObjA[2] - gObjB[2], 2))

#credit to Anthony Church for this function
def lockHideAttr(obj,attrArray,lock,hide):
    for a in attrArray:
        mc.setAttr(obj + '.' + a, k=hide,l=lock)

#searches for a digits in a string and returns the digits found in that string as a string. If no digits found, return False
def getDigits(str1):
    c = ''
    for i in str1:
        if i.isdigit():
            c += i
    if c == '':
        return False
    else:
        return c


def orientationNormal(axis):

    # make axis upper case in case we enter x, y, or z
    axis = axis.upper()

    # if orientation isnt x, y, or z, spit out error
    if 'X' not in axis and 'Y' not in axis and 'Z' not in axis:
        mc.error('Orientation can only be x, y, or z.')

    # translating axis string to vector list
    if axis == 'X':
        aimVector = [1, 0, 0]

    if axis == 'Y':
        aimVector = [0, 1, 0]

    if axis == 'Z':
        aimVector = [0, 0, 1]

    if axis == '-X':
        aimVector = [-1, 0, 0]

    if axis == '-Y':
        aimVector = [0, -1, 0]

    if axis == '-Z':
        aimVector = [0, 0, -1]

    return aimVector


#check if something exists, if it does, warn us and delete it
def checkExists(*args):
    for check in args:
        if mc.objExists(check):
            mc.warning('DELETING an existing \"' + check + '\", double check to ensure names were not the same.')
            mc.delete(check)


# function to send rotate values to joint orient.
def rotateToJointOrient(list):

    # if the list is a string, make it a list
    list = stringIntoList(list)

    for object in list:
        # get rotation values of joint
        rx = mc.getAttr(object + '.rx')
        ry = mc.getAttr(object + '.ry')
        rz = mc.getAttr(object + '.rz')

        # set joint orient values to rotation values
        mc.setAttr(object + '.jointOrientX', rx)
        mc.setAttr(object + '.jointOrientY', ry)
        mc.setAttr(object + '.jointOrientZ', rz)

        # set rotation values to zero
        mc.xform(object, ro=[0, 0, 0])
        mc.select(cl=True)

    return list

#makes a joint chain based on *args given. also give it a parent if you want it to be parented, and a prefix for the joints
def makeJointChain(theParent, prefix, name):

    list = mc.listRelatives(name, ad=True, type='transform')
    list.reverse()


    jointList = []

    #gets objecs position, makes a joint on that position, add it to the jointList for us to return later
    for locator in list:

        if 'AIMloc_' in locator:
            writeJson(os.environ["RDOJO_DATA"] + '/aim.json', locator)
            list.remove(locator)
            print 'removed locator from list, here is the list:'
            print list

    for locator in list:
            mc.select(locator)
            mc.setToolTo('Move')
            locatorPosition = mc.manipMoveContext('Move', q=True, p=True)
            aJoint = mc.joint(n=prefix + locator, p=locatorPosition)
            jointList.append(aJoint)
            mc.parent(locator, 'extras_grp')
            mc.select(cl=True)


    #if the parent you specified exists, parent the joints to that object
    if mc.objExists(theParent) == True:

        for object in list:
            mc.parent(prefix + object, theParent)

    else:

        for object in list:
            mc.parent(prefix + object, w=True)

    print jointList
    mc.delete(name)
    writeJson(os.environ["RDOJO_DATA"] + '/data.json', jointList)
    return jointList

#orients the objects in list. Note: ordering is based on order of list. also takes what direction you would like it to be oriented
def orientChain(list, orientation='x'):

    aimVector = orientationNormal(orientation)

    #aim the joint to the next joint in the list, then delete the aim constraint
    for x in range(len(list)):
        if list[x] != list[-1]:
            mc.aimConstraint(list[x + 1], list[x], mo=False, aim=aimVector)
            mc.select(list[x])
            mc.delete(mc.listRelatives(type="aimConstraint"))
            mc.select(cl=True)

    return list

#function to parent a list based on the order in the list
def parentChain(list):

    for x in reversed(range(len(list))):
        if list[x] != list[0]:
            mc.parent(list[x], list[x - 1])

    mc.setAttr(list[-1] + '.jointOrientX', 0)
    mc.setAttr(list[-1] + '.jointOrientY', 0)
    mc.setAttr(list[-1] + '.jointOrientZ', 0)

    mc.select(cl=True)


#function to aim the end of a list to the end aim locator.
def aimEnd(list, orientation='x'):
    #load the last aim loc that we made into a variable
    aimLoc = json.loads(readJson(os.environ["RDOJO_DATA"] + '/aim.json'))

    #if it exists, orient the last object of the list to that aim locator, then delete the aim locator.
    if mc.objExists(aimLoc) == True:
        orientList = [list[-1], aimLoc]
        orientChain(orientList, orientation)
        mc.delete(aimLoc)

# function to make a quad arrow
def create_quad_arrow(name):
    control = mc.curve(d=1,
                       p=[(1, 0, 1), (3, 0, 1), (3, 0, 2), (5, 0, 0), (3, 0, -2), (3, 0, -1), (1, 0, -1), (1, 0, -3),
                          (2, 0, -3), (0, 0, -5), (-2, 0, -3), (-1, 0, -3), (-1, 0, -1), (-3, 0, -1), (-3, 0, -2),
                          (-5, 0, 0), (-3, 0, 2), (-3, 0, 1), (-1, 0, 1), (-1, 0, 3), (-2, 0, 3), (0, 0, 5), (2, 0, 3),
                          (1, 0, 3), (1, 0, 1), ],
                       k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    mc.rename(name)
    # center pivot
    mc.xform(cp=True)
    # freeze transformation
    mc.makeIdentity(apply=True, t=True, r=True, s=True)
    # clear selection
    mc.select(cl=True)

    return name


def organizationGroup():

    # makes a group for the arm rig and generates the global cntrl with an FK IK attribute, an FK stretch, and volumetric
    mc.group(n='rig_grp', em=True, w=True)
    create_quad_arrow('global_cntrl')

    # parent and group hierarchy to keep everything organized
    mc.parent('global_cntrl', 'rig_grp')

    #make geo_grp, rig_grp, IK_grp, joints_grp, cntrl_grp
    mc.group(n='geo_grp', em=True, p='rig_grp')
    mc.group(n='extras_grp', em=True, p='rig_grp')
    mc.group(n='IK_grp', em=True, p='global_cntrl')
    mc.group(n='joints_grp', em=True, p='global_cntrl')
    mc.group(n='cntrl_grp', em=True, p='global_cntrl')
    mc.setAttr('extras_grp.visibility', 0)
    mc.select(cl=True)


def organizationGroupExists():
    conditionList = []
    conditionList.append(mc.objExists('rig_grp'))
    conditionList.append(mc.objExists('global_cntrl'))
    conditionList.append(mc.objExists('geo_grp'))
    conditionList.append(mc.objExists('extras_grp'))
    conditionList.append(mc.objExists('IK_grp'))
    conditionList.append(mc.objExists('joints_grp'))
    conditionList.append(mc.objExists('cntrl_grp'))

    if all(conditionList) == True:
        return all(conditionList)
    elif any(conditionList) == True:
        mc.error(
            'rig_grp, global_cntrl, geo_grp, extras_grp, IK_grp, joints_grp, or cntrl_grp already exist. Please rename or delete.')
    else:
        return all(conditionList)


# function to duplicate an object and its children and assign new names
def duplicateNewName(object, search, replace, colour):
    childList = []

    # this is the list of all the children of object we will be duplicating
    checkList = mc.listRelatives(object, ad=True, f=False, type='transform')
    checkList.reverse()

    # name for our new object
    newObject = object.replace(search, replace)

    # duplicate the original and name it accordingly, rename all the children for unique names
    mc.duplicate(object, n=newObject, rc=True)

    # change the color
    if colour is not "none":
        mc.setAttr(newObject + '.overrideEnabled', 1)
        mc.setAttr(newObject + '.overrideColor', colour)

    # get the children of the new object
    children = mc.listRelatives(newObject, ad=True, f=False, type='transform')
    children.reverse()

    # rename the children with the search and replace parameters
    for child in children:
        newName = child.replace(search, replace)
        mc.rename(child, newName)
        childList.append(newName)

    # when we duplicated our object, we renamed all our children with unique names, but we want them to share the same names.
    # this checks the original children and the duplicate children's and matches the digits of the duplicate to the original
    for check, child in zip(checkList, childList):

        if getDigits(check) == False and type(getDigits(child)) != bool:
            newName1 = child.replace(getDigits(child), '')
            mc.rename(child, newName1)

        elif type(getDigits(check)) != bool and type(getDigits(child)) != bool:
            if getDigits(check) != getDigits(child):
                newName2 = child.replace(getDigits(child), getDigits(check))
                mc.rename(child, newName2)

    # insert our duplicate object into the list as the first object in the list so that it is in order
    returnList= mc.listRelatives(newObject, ad=True, f=False, type='transform')
    returnList.reverse()
    returnList.insert(0, newObject)

    return returnList


# make controls based on the hierarchy of a list
def cntrlHierarchy(list, radius, colour, orientation='x', toParent='cntrl_grp'):

    cntrlList = []
    aimVector = orientationNormal(orientation)

    #if the list is a string, make it a list
    list = stringIntoList(list)

    for object in list:
        # make a new control for object. Get the parent of the joint so that we know the order and in case it returns "None".
        cntrl = mc.circle(n=object + '_cntrl', nr=aimVector, r=radius)
        objectParent = mc.listRelatives(object, p=True)

        # create an empty node and parent constraint it to the object to match position and orientation
        mc.parentConstraint(object, mc.createNode('transform', n='offset_' + object))
        mc.delete(mc.listRelatives(type='parentConstraint'))
        mc.delete('offset_' + object, ch=True)
        mc.select(cl=True)

        # parent constraint the control to the object for positionoing and orientation freeze transforms, delete history
        mc.parentConstraint(object, object + '_cntrl')
        mc.delete(mc.listRelatives(object + '_cntrl', type='parentConstraint'))
        mc.parent(object + '_cntrl', 'offset_' + object)
        mc.makeIdentity(object + '_cntrl', apply=True, t=True, r=True, s=True)
        mc.delete(object + '_cntrl', ch=True)

        # set the color
        mc.setAttr(object + '_cntrl' + '.overrideEnabled', 1)
        mc.setAttr(object + '_cntrl' + '.overrideColor', colour)

        # for the next part to work, we need the cntrls to be in the same order as the objects, so put the cntrls in a list
        cntrlList.append(cntrl[0])

    for object, cntrl in zip(list, cntrlList):

        objectParent = mc.listRelatives(object, p=True)

        # if the parent of selection is in the cntrl list, parent the cntrl to the according offset (it should be the parent in the hierarchy + "cntrl")
        if objectParent is not None and objectParent[0] in list:
            mc.parent('offset_' + object, objectParent[0] + '_cntrl')

    # parent the root of the cntrls to specified parent
    if toParent is not "none":
        mc.parent(getRoot(cntrlList[0]), toParent)

    return cntrlList


# a function to make empty group nodes to serve as offsets
def offsetCreator(list):

    # if the list is a string, make it a list
    list = stringIntoList(list)

    for object in list:

        mc.select(cl=True)
        mc.select(object)

        # get the objectsParent
        objectParent = mc.listRelatives(object, p=True)

        # create a empty transform node and parent it to the object to position and orient
        mc.parentConstraint(object, mc.createNode('transform', n='offset_' + object))
        mc.delete(mc.listRelatives(type='parentConstraint'))
        mc.makeIdentity('offset_' + object, apply=True, t=True, r=True, s=True)
        mc.delete('offset_' + object, ch=True)
        mc.select(cl=True)

        # if the object has a parent, parent the offset under the object parents, and the parent the object under the offset
        if objectParent is not None:
            mc.parent('offset_' + object, objectParent)
            mc.parent(object, 'offset_' + object)

        # if the object doesnt have a parent it means that it is already in worldspace, in which case, just parent the object to the offset
        elif objectParent is None:
            mc.parent(object, 'offset_' + object)


#function to blend in between two chains.
def blendThree(list1, list2, list3, controlToAttribute, attributeLongName, fullName):

    # if the lists arent the same length, spit out a warning
    if len(list1) != len(list2) or len(list1) != len(list3):
        mc.error('The lists in blendThree dont have the same amount of objects')

    attributeLongName = fullName + '_' + attributeLongName

    # add the attribute to the specified object
    mc.addAttr(controlToAttribute, ln=attributeLongName, at='float', dv=0, min=0, max=1, w=True, r=True, k=True)

    # list of the blend nodes we are about to make
    blendNodes = []
    attributes = ['translate', 'rotate', 'scale']

    for object, object2, object3 in zip(list1, list2, list3):
        for attr in attributes:

            #name our good stuff
            blendAttrName = object + '_' + attr + '_' + attributeLongName + 'blend'

            #check to make sure our object doesnt already exist
            checkExists(blendAttrName)

            # for all the objects in the list, make a translate and rotate blending node
            mc.shadingNode('blendColors', n=blendAttrName, au=True)

            # add the blending nodes to the list
            blendNodes.append(blendAttrName)

            # connect the blends output to the list1
            mc.connectAttr(blendAttrName + '.output', object + '.' + attr)

            # connect list 2 to the blends color2
            mc.connectAttr(object2 + '.' + attr, blendAttrName + '.color2')

            # connect list 3 to blends color 1
            mc.connectAttr(object3 + '.' + attr, blendAttrName + '.color1')

    for node in blendNodes:
        # connect the attribute we made to all of the blendColors "blender" attribute
        mc.connectAttr(controlToAttribute + '.' + attributeLongName, node + '.blender')



# function to constrain two lists, choose if you want a point, orient, and or scale constraint
def constrainLists(list1, list2, point, orient, size):

    # if the list is a string, make it a list
    list1 = stringIntoList(list1)
    list2 = stringIntoList(list2)

    # if statement in case you dont want a constraint
    if point is not 'none':

        # constraint the object of one list to the object of the other list
        for object1, object2 in zip(list1, list2):
            mc.pointConstraint(object1, object2, mo=False)

    if orient is not 'none':

        for object1, object2 in zip(list1, list2):
            mc.orientConstraint(object1, object2, mo=False)

    if size is not 'none':

        for object1, object2 in zip(list1, list2):
            mc.scaleConstraint(object1, object2, mo=False)

#takes two lists, the cntrl and the joint list and connects the scale values of the two in an FK volumetric scaling way
def volumetricFK(list1, list2, orientation='x'):

    #make orientation be upper case in case that its not
    orientation = orientation.upper()

    #if the cntrl list and the joint list dont have the same amount of objects, spit out a warning
    if len(list1) != len(list2):
        mc.warning('The two lists dont have the same amount of objects')

    #if the orientation isnt x, y, or z, spit out a warning
    if orientation != 'X' and orientation != 'Y' and orientation != 'Z':
        mc.warning('Orientation can only be x, y, or z.')

    #translating orientation to rgb for our blend colors node later on
    if orientation == 'X':
        orientationColor = 'R'
        oc2 = 'G'
        oc3 = 'B'

    elif orientation == 'Y':
        orientationColor = 'G'
        oc2 = 'R'
        oc3 = 'B'

    elif orientation == 'Z':
        orientationColor = 'B'
        oc2 = 'R'
        oc3 = 'G'


    for cntrl in list1:

        multDivName = cntrl + '_FKstretch_inverse'
        blendName = cntrl + '_FKstretch_blend'

        checkExists(multDivName, blendName)

        #make our multiply divide that will be the inverse of x, and our blend colors node
        mc.shadingNode('multiplyDivide', n=multDivName, au=True)
        mc.shadingNode('blendColors', n=blendName, au=True)

        #set the operation of the multDiv to be division, and set input1x to be 1
        mc.setAttr(cntrl + '_FKstretch_inverse.operation', 2)
        mc.setAttr(cntrl + '_FKstretch_inverse.input1X', 1)

        #add an attribute to every control called volumetric to be used as our blender
        mc.addAttr(cntrl, ln='volumetric', at='float', dv=1, min=0, max=1, w=True, r=True, k=True)
        mc.connectAttr(cntrl + '.volumetric', cntrl + '_FKstretch_blend.blender')

        #connect our cntrl's scale X, Y, or Z into the multDiv to get the inverse to plug into the blend colors
        mc.connectAttr(cntrl + '.scale' + orientation, cntrl + '_FKstretch_inverse.input2X')

        #connect our cntrl;s scale X, Y, or Z into blender color1 R, G, or B
        mc.connectAttr(cntrl + '.scale' + orientation, cntrl + '_FKstretch_blend.color1' + orientationColor)
        mc.connectAttr(cntrl + '_FKstretch_inverse.outputX', cntrl + '_FKstretch_blend.color1' + oc2)
        mc.connectAttr(cntrl + '_FKstretch_inverse.outputX', cntrl + '_FKstretch_blend.color1' + oc3)

        #connect our cntrl's scale into blend color 2
        mc.connectAttr(cntrl + '.scale', cntrl + '_FKstretch_blend.color2')

    for cntrl, FKjoint in zip(list1, list2):

        #connect the output of the blender into the FK joint
        mc.connectAttr(cntrl + '_FKstretch_blend.output', FKjoint + '.scale')

#function that returns the top parent and end child of a hierarchy
def getEnds(list):

    returnList = []
    theParent = ''
    theChild = ''

    #if the parent of the object is none, then it must be the parent! but what if its parent is the world?
    for object in list:
        if mc.listRelatives(object, p=True) is None:
            theParent = object

    #if the parent is the world, then go through the list again and make the parent the uppermost in the hierarchy
    if theParent == '':
        for object in list:
            if mc.listRelatives(object, p=True)[0] not in list:
                theParent = object

    # if the child of the object is none, then it must be the child! but what if the child has a child and its never none?
    for object in list:
        if mc.listRelatives(object, c=True) is None:
            theChild = object

    #if theChild is still empty, make the child the one without a child in the list
    if theChild == '':
        for object in list:
            if mc.listRelatives(object, c=True)[0] not in list:
                theChild = object

    #the returnList will return the parent first then the child
    returnList.append(theParent)
    returnList.append(theChild)

    if returnList[0] == returnList[1]:
        mc.warning('list is not in a hierarchy!')
    else:
        return returnList


#function to make an IK based on the IK joint chain
def makeIK(IK_joints, IK_cntrl):

    #turn IK_cntrl into a list in case we pass a string
    stringIntoList(IK_cntrl)

    # make an IK handle based on the joint chain given to us
    if len(IK_joints) >= 4:
        mel.eval('ikSpringSolver;')
        IKhandle = \
        mc.ikHandle(n=IK_cntrl[0] + '_handle', sj=getEnds(IK_joints)[0], ee=getEnds(IK_joints)[1],
                    sol='ikSpringSolver')[0]

        mc.setAttr(IKhandle + '.poleVectorX', 1)
        mc.setAttr(IKhandle + '.poleVectorY', 0)
        mc.setAttr(IKhandle + '.poleVectorZ', 1)
    else:
        IKhandle = mc.ikHandle(n=IK_cntrl[0] + '_handle', sj=getEnds(IK_joints)[0], ee=getEnds(IK_joints)[1], sol='ikRPsolver', pw=1, w=1)[0]

    #parent the ik handle to IK_grp
    mc.parent(IKhandle, 'IK_grp')

    #add a twist attribute to our cntrl, connect it, and connect our cntrl to our IK joint and IK handle
    mc.addAttr(IK_cntrl[0], ln='twist', at='float', dv=0, w=True, r=True, k=True)
    mc.connectAttr(IK_cntrl[0] + '.twist', IKhandle + '.twist')
    mc.orientConstraint(IK_cntrl[0], getEnds(IK_joints)[1], mo=False)
    mc.pointConstraint(IK_cntrl[0], IKhandle)

#function that takes the IK cntrl, IK_joints, and the orientation for the stretchyness
def stretchyIK(IK_cntrls, IK_joints, orientation='x', global_cntrl='global_cntrl'):

    # make orientation uppercase to match syntax
    orientation = orientation.upper()

    # if the orientation isnt x, y, or z, spit out a warning
    if orientation != 'X' and orientation != 'Y' and orientation != 'Z':
        mc.warning('Orientation can only be x, y, or z.')

    # in case we pass a string in IK_cntrls, make IK_cntrls a list
    IK_cntrls = stringIntoList(IK_cntrls)

    # variables for later use
    distances = []
    distanceTotal = 0.0

    for x in range(len(IK_joints) - 1):
        distances.append(getDistance(IK_joints[x], IK_joints[x + 1]))

    for x in distances:
        distanceTotal = distanceTotal + x

    distanceNode = mc.distanceDimension(sp=mc.xform(IK_joints[0], q=True, t=True, ws=True),
                                        ep=mc.xform(IK_joints[-1], q=True, t=True, ws=True))
    mc.parent(mc.listRelatives(distanceNode, p=True)[0], 'extras_grp')

    mc.pointConstraint(IK_joints[0], mc.listConnections(distanceNode)[0], mo=False)
    mc.pointConstraint(IK_cntrls[0], mc.listConnections(distanceNode)[1], mo=False)

    # our four variables we will be working with
    IK_stretch = IK_cntrls[0] + '_IKstretch'
    conditionNode = IK_cntrls[0] + '_stretchCondition'
    globalScale = IK_cntrls[0] + '_IKstretch_globalScale'
    blender = IK_cntrls[0] + '_IKstretch_blend'

    # make sure our variables didnt exist before
    checkExists(IK_stretch, conditionNode, globalScale, blender)

    # ik stretch connections
    mc.shadingNode('multiplyDivide', n=IK_stretch, au=True)
    mc.setAttr(IK_stretch + '.operation', 2)
    mc.connectAttr(distanceNode + '.distance', IK_stretch + '.input1X')

    # condition node connections
    mc.shadingNode('condition', n=conditionNode, au=True)
    mc.setAttr(conditionNode + '.operation', 3)
    mc.connectAttr(distanceNode + '.distance', conditionNode + '.firstTerm')
    mc.connectAttr(IK_stretch + '.outputX', conditionNode + '.colorIfTrueR')

    # global scale mult connections
    mc.shadingNode('multiplyDivide', n=globalScale, au=True)
    mc.setAttr(globalScale + '.input1X', distanceTotal)
    mc.connectAttr(global_cntrl + '.scaleX', globalScale + '.input2X')
    mc.connectAttr(globalScale + '.outputX', conditionNode + '.secondTerm')
    mc.connectAttr(globalScale + '.outputX', IK_stretch + '.input2X')

    # blender connections
    mc.shadingNode('blendColors', n=blender, au=True)
    mc.addAttr(IK_cntrls[0], ln='Stretch', at='float', dv=1, min=0, max=1, w=True, r=True, k=True)
    mc.setAttr(blender + '.color2R', 1)
    mc.connectAttr(IK_cntrls[0] + '.Stretch', blender + '.blender')
    mc.connectAttr(conditionNode + '.outColorR', blender + '.color1R')

    # connect the output of the blender to all the specified scale attrs of the IK joints
    for x in range(len(IK_joints) - 1):
        mc.connectAttr(blender + '.outputR', IK_joints[x] + '.scale' + orientation)


#function to figure out the placement based on given orientation and distance
def evaluate(ori, alt, oriDistance, aimDistance, o, k):

    if '-' in ori:
        o = int(o) - int(oriDistance)
        if alt == True:
            if k == aimDistance:
                k = 0
            else:
                k = aimDistance
    else:
        o = int(o) + int(oriDistance)
        if alt == True:
            if k == aimDistance:
                k = 0
            else:
                k = aimDistance

    returnList = []
    returnList.append(o)
    returnList.append(k)

    #return a list with o and k which are values
    return returnList

